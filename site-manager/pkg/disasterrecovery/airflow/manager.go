package airflow

import (
	"context"
	"fmt"
	"github.com/Netcracker/qubership-disaster-recovery-daemon/api/entity"
	"github.com/golang/glog"
	"github.com/pkg/errors"
	v12 "k8s.io/api/apps/v1"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"

	k8s "site-manager/pkg/kubernetes/utils"
	t "site-manager/pkg/types"
	"sync"
	"time"
)

type DRManager struct {
	namespace             string
	startTimeout          int
	shutdownTimeout       int
	componentToReplicaMap map[string]int
	clientSet             *kubernetes.Clientset
}

const (
	tierLabel = "tier=airflow"
)

func NewDRManager(cfg t.Config, clientSet *kubernetes.Clientset) DRManager {
	glog.Info("Initializing Airflow DR DRManager")

	controller := DRManager{
		namespace:             cfg.Namespace,
		startTimeout:          cfg.StartTimeout,
		shutdownTimeout:       cfg.ShutdownTimeout,
		componentToReplicaMap: cfg.ReplicaMap,
		clientSet:             clientSet,
	}
	return controller
}

func (m DRManager) HealthAirflow(request entity.HealthRequest) (entity.HealthResponse, error) {
	glog.Info("Received /healthz request")
	if airflowStatus, err := m.getAirflowStatus(); err == nil {
		glog.Infof("Airflow health status: %s", airflowStatus)
		return entity.HealthResponse{Status: airflowStatus.Status}, nil
	} else {
		return entity.HealthResponse{}, err
	}
}

func (m *DRManager) getComponentStatus(labelName string, labelValue string, replicas int) (status int) {
	glog.V(4).Infof("Checking component %s status", labelValue)
	status = 10000
	readyPods := 0
	labelSelector := fmt.Sprintf("%s=%s", labelName, labelValue)
	pods, err := m.clientSet.CoreV1().Pods(m.namespace).List(context.TODO(), metav1.ListOptions{LabelSelector: labelSelector, FieldSelector: "status.phase=Running"})

	if pods != nil && len(pods.Items) > 0 {
		for _, pod := range pods.Items {
			if ready, err := k8s.PodRunningAndReady(pod); err == nil && ready {
				readyPods += 1
			}
		}
	}

	if err == nil {
		if readyPods == replicas && readyPods > 0 {
			status = 1
			glog.V(4).Infof("Component %s status is UP", labelValue)
		}
		if readyPods == 0 {
			status = 0
			glog.V(4).Infof("Component %s status is DOWN", labelValue)
		}
		if readyPods > 0 && readyPods < replicas {
			status = -10
			glog.V(4).Infof("Component %s status is DEGRADED", labelValue)
		}
		if readyPods > replicas {
			glog.Warningf("Component %s has more replicas than specified", labelValue)
		}
	}
	if err != nil {
		glog.Errorf("Could not get pods with labels %s in namespace `%v`.", labelSelector, m.namespace)
	}
	return status
}

func (m *DRManager) isComponentUp(labelName string, labelValue string) (isUp bool) {
	return m.getComponentStatus(labelName, labelValue, m.componentToReplicaMap[labelValue]) == 1
}

func (m *DRManager) hasRunningPods(labelName string, labelValue string) (hasRunningPods bool) {
	glog.Infof("Checking if deployment %s has running pods", labelValue)
	pods, err := m.clientSet.CoreV1().Pods(m.namespace).List(context.TODO(), metav1.ListOptions{})
	for _, pod := range pods.Items {
		labels := pod.Labels
		if labels[labelName] == labelValue {
			if pod.Status.Phase == v1.PodRunning {
				hasRunningPods = true
				break
			}
		}
	}
	if err != nil {
		glog.Errorf("Could not get pods in namespace `%v`.", m.namespace)
	}
	glog.Infof("Deployment %s has running pods: %v", labelValue, hasRunningPods)
	return hasRunningPods
}

func (m *DRManager) getAirflowStatus() (airflowStatus t.AirflowStatus, err error) {
	airflowStatus = t.AirflowStatus{Status: "down"}
	componentsStatus := 1
	for componentName, replicas := range m.componentToReplicaMap {
		if componentName == "flower" || componentName == "statsd" {
			continue
		}
		if componentName == "worker" && !m.isComponentDeployed("component", "worker") {
			continue
		}
		componentsStatus *= m.getComponentStatus("component", componentName, replicas)
		if componentsStatus == 0 {
			airflowStatus.Status = "down"
			break
		}
		if componentsStatus < 0 {
			airflowStatus.Status = "degraded"
			break
		}
	}

	if componentsStatus == 1 {
		airflowStatus.Status = "up"
	}

	if m.isComponentDeployed("component", "flower") {
		flowerStatus := m.getComponentStatus("component", "flower", m.componentToReplicaMap["flower"])

		if componentsStatus == 1 && flowerStatus != 1 {
			airflowStatus.Status = "degraded"
		}
	}

	if m.isComponentDeployed("component", "statsd") {
		statsdStatus := m.getComponentStatus("component", "statsd", m.componentToReplicaMap["statsd"])

		if componentsStatus == 1 && statsdStatus != 1 {
			airflowStatus.Status = "degraded"
		}
	}

	return airflowStatus, err
}

func (m *DRManager) isComponentDeployed(labelName string, labelValue string) (isDeployed bool) {
	glog.V(4).Infof("Checking if the %s is deployed", labelValue)
	isDeployed = true
	deployment, err := k8s.GetDeployment(m.clientSet, m.namespace, labelName, labelValue)
	if err != nil {
		glog.Info("Could not get %s deployment.", labelValue)
		isDeployed = false
	} else {
		if deployment.UID == "" {
			glog.Infof("Could not get %s deployment. Probably it is not deployed.", labelValue)
			isDeployed = false
		}
	}
	return isDeployed
}

func (m DRManager) ChangeMode(controllerRequest entity.ControllerRequest) (resp entity.ControllerResponse, err error) {
	glog.V(3).Infof("Started DR mode changing process to %v", controllerRequest.Mode)
	resp = entity.ControllerResponse{}
	switch controllerRequest.Mode {
	case entity.STANDBY, entity.DISABLED:
		var deploymentsList *v12.DeploymentList
		var statefulSetsList *v12.StatefulSetList
		var wgScale sync.WaitGroup
		var wgDown sync.WaitGroup
		scaleDownCh := make(chan error)
		waitScaleDownCh := make(chan error)

		go func() {
			if deploymentsList, err = k8s.ListDeployments(m.clientSet, m.namespace, tierLabel); err == nil {
				for _, deployment := range deploymentsList.Items {
					componentLabel := deployment.Labels["component"]
					wgScale.Add(1)
					go func() {
						defer wgScale.Done()
						k8s.ScaleDeployment(m.clientSet, m.namespace, "component", componentLabel, 0, scaleDownCh)
					}()

				}
				if statefulSetsList, err = k8s.ListStatefulSets(m.clientSet, m.namespace, tierLabel); err == nil {
					for _, statefulSet := range statefulSetsList.Items {
						componentLabel := statefulSet.Labels["component"]
						wgScale.Add(1)
						go func() {
							defer wgScale.Done()
							k8s.ScaleStatefulSet(m.clientSet, m.namespace, "component", componentLabel, 0, scaleDownCh)
						}()
					}
				}
				glog.V(2).Info("Waiting for Airflow components replicas to update for scale down")
				wgScale.Wait()
				close(scaleDownCh)

				//---wait to scale down
				go func() {
					for _, deployment := range deploymentsList.Items {
						componentLabel := deployment.Labels["component"]
						wgDown.Add(1)
						go func() {
							defer wgDown.Done()
							m.waitForComponentToScaleDown("component", componentLabel, waitScaleDownCh)
						}()
					}
					if statefulSetsList, err = k8s.ListStatefulSets(m.clientSet, m.namespace, tierLabel); err == nil {
						for _, statefulSet := range statefulSetsList.Items {
							componentLabel := statefulSet.Labels["component"]
							wgDown.Add(1)
							go func() {
								defer wgDown.Done()
								m.waitForComponentToScaleDown("component", componentLabel, waitScaleDownCh)
							}()
						}
					}
					glog.V(2).Info("Waiting for Airflow to scale Down")
					wgDown.Wait()

					//---deleting KubernetesExecutor pods
					m.shutDownKuberWorkers(waitScaleDownCh)

					close(waitScaleDownCh)
				}()
			}
		}()
		for errorFromChan := range scaleDownCh {
			if errorFromChan != nil {
				err = errorFromChan
				glog.Errorf("Error while setting replicas to update for scale down. %v", err)
				break
			}
		}

		if err == nil {
			for errorFromChan := range waitScaleDownCh {
				if errorFromChan != nil {
					err = errorFromChan
					glog.Errorf("Error while waiting components to scale down. %v", err)
					break
				}
			}
		}

		if err == nil {
			resp = entity.ControllerResponse{
				SwitchoverState: entity.SwitchoverState{
					Mode:    controllerRequest.Mode,
					Status:  entity.DONE,
					Comment: "Switchover successfully done",
				},
			}
			glog.Infof("Successfully changed to mode %v", controllerRequest.Mode)
		} else {
			resp = entity.ControllerResponse{
				SwitchoverState: entity.SwitchoverState{
					Mode:    controllerRequest.Mode,
					Status:  entity.FAILED,
					Comment: "Switchover failed",
				},
			}
			glog.Errorf("Failed changing to mode %v. %v", controllerRequest.Mode, err)
		}
	case entity.ACTIVE:
		var deploymentsList *v12.DeploymentList
		var statefulSetsList *v12.StatefulSetList
		var wgScale sync.WaitGroup
		var wgUp sync.WaitGroup
		scaleUpCh := make(chan error)
		waitScaleUpCh := make(chan error)

		go func() {
			if deploymentsList, err = k8s.ListDeployments(m.clientSet, m.namespace, tierLabel); err == nil {
				for _, deployment := range deploymentsList.Items {
					componentLabel := deployment.Labels["component"]
					wgScale.Add(1)
					go func() {
						defer wgScale.Done()
						k8s.ScaleDeployment(m.clientSet, m.namespace, "component", componentLabel, int32(m.componentToReplicaMap[componentLabel]), scaleUpCh)
					}()
				}
				if statefulSetsList, err = k8s.ListStatefulSets(m.clientSet, m.namespace, tierLabel); err == nil {
					for _, statefulSet := range statefulSetsList.Items {
						componentLabel := statefulSet.Labels["component"]
						wgScale.Add(1)
						go func() {
							defer wgScale.Done()
							k8s.ScaleStatefulSet(m.clientSet, m.namespace, "component", componentLabel, int32(m.componentToReplicaMap[componentLabel]), scaleUpCh)
						}()
					}
				}
				glog.V(2).Info("Waiting for Airflow components replicas to update for scale up")
				wgScale.Wait()
				close(scaleUpCh)

				//----wait for scale up
				go func() {
					for _, deployment := range deploymentsList.Items {
						componentLabel := deployment.Labels["component"]
						wgUp.Add(1)
						go func() {
							defer wgUp.Done()
							m.waitForComponentToScaleUp("component", componentLabel, waitScaleUpCh)
						}()
					}
					if statefulSetsList, err = k8s.ListStatefulSets(m.clientSet, m.namespace, tierLabel); err == nil {
						for _, statefulSet := range statefulSetsList.Items {
							componentLabel := statefulSet.Labels["component"]
							wgUp.Add(1)
							go func() {
								defer wgUp.Done()
								m.waitForComponentToScaleUp("component", componentLabel, waitScaleUpCh)
							}()
						}
					}
					glog.V(2).Info("Waiting for Airflow to scale Up")
					wgUp.Wait()
					close(waitScaleUpCh)
				}()
			}
		}()

		for errorFromChan := range scaleUpCh {
			if errorFromChan != nil {
				err = errorFromChan
				glog.Errorf("Error while waiting components replicas to update for scale Up. %v", err)
				break
			}
		}

		if err == nil {
			for errorFromChan := range waitScaleUpCh {
				if errorFromChan != nil {
					err = errorFromChan
					glog.Errorf("Error while waiting components to scale up. %v", err)
					break
				}
			}
		}

		if err == nil {
			resp = entity.ControllerResponse{
				SwitchoverState: entity.SwitchoverState{
					Mode:    controllerRequest.Mode,
					Status:  entity.DONE,
					Comment: "Switchover successfully done",
				},
			}
			glog.Infof("Successfully changed to mode %v", controllerRequest.Mode)
		} else {
			resp = entity.ControllerResponse{
				SwitchoverState: entity.SwitchoverState{
					Mode:    controllerRequest.Mode,
					Status:  entity.FAILED,
					Comment: "Switchover failed",
				},
			}
			glog.Errorf("Failed changing to mode %v. %v", controllerRequest.Mode, err)
		}
	default:
		resp = entity.ControllerResponse{
			SwitchoverState: entity.SwitchoverState{
				Mode:    controllerRequest.Mode,
				Status:  entity.FAILED,
				Comment: "Switchover failed. Only standby and active modes are supported.",
			},
		}
		glog.Infof("Failed changing to mode %v. This mode is not supported.", controllerRequest.Mode)
		err = errors.New("Requested mode is not supported")
	}
	return resp, err
}

func (m DRManager) shutDownKuberWorkers(ch chan error) {
	glog.Info("Shutting down Kubernetes Executor Workers")
	pods, err := k8s.ListPods(m.clientSet, m.namespace, "component=worker,kubernetes_executor=True")
	if err == nil {
		for _, pod := range pods.Items {
			if err = m.clientSet.CoreV1().Pods(m.namespace).Delete(context.TODO(), pod.Name, metav1.DeleteOptions{}); err != nil {
				ch <- errors.WithMessagef(err, "Could not delete Kubernetes Executor Worker pod %v", pod.Name)
			} else {
				glog.Infof("Deleted Kubernetes Executor Worker pod %v", pod.Name)
			}
		}
	}
	if err != nil {
		ch <- errors.WithMessagef(err, "Could not get Kubernetes Executor Worker pods")
	}
}

func (m DRManager) waitForComponentToScaleDown(labelName string, labelValue string, ch chan error) {
	glog.Infof("Waiting for component %s=%s to scale down", labelName, labelValue)
	isDown := false
	err := wait.Poll(time.Second, time.Duration(m.shutdownTimeout)*time.Second, func() (done bool, err error) {
		if m.isComponentUp(labelName, labelValue) {
			glog.V(3).Infof("Component %s=%s still has running pods", labelName, labelValue)
			isDown = false
			return isDown, err
		} else {
			glog.V(3).Infof("Component %s=%s is scaled down", labelName, labelValue)
			isDown = true
			return isDown, err
		}
	})
	if err == nil {
		if isDown {
			glog.Infof("Component %s=%s is down", labelName, labelValue)
		} else {
			glog.Infof("Component %s=%s is up", labelName, labelValue)
		}
	}
	ch <- errors.WithMessagef(err, "Error while waiting %s=%s to scale down", labelName, labelValue)
}

func (m DRManager) waitForComponentToScaleUp(labelName string, labelValue string, ch chan error) {
	glog.Infof("Waiting for deployment %s=%s to scale up", labelName, labelValue)
	isUp := false
	err := wait.Poll(time.Second, time.Duration(m.startTimeout)*time.Second, func() (done bool, err error) {
		if m.isComponentUp(labelName, labelValue) {
			glog.V(3).Infof("Component %s=%s is up", labelName, labelValue)
			isUp = true
			return isUp, err
		} else {
			glog.V(3).Infof("Component %s=%s is scaled down", labelName, labelValue)
			isUp = false
			return isUp, err
		}
	})
	if err == nil {
		if isUp {
			glog.Infof("Component %s=%s is up", labelName, labelValue)
		} else {
			glog.Infof("Component %s=%s is down", labelName, labelValue)
		}
	}

	ch <- errors.WithMessagef(err, "Error while waiting %s=%s to scale up", labelName, labelValue)
}

func (m DRManager) retryGetDeployment(err error) bool {
	if err != nil {
		glog.Errorf("Got error while site-manager status initialization. Will retry. %v", err)
		return true
	} else {
		return false
	}
}

//func getEnvInt(paramName string, defaultValue int) int {
//	value := defaultValue
//	if envValue, err := strconv.Atoi(os.Getenv(paramName)); err != nil {
//		glog.Errorf("Could not get %v env variable. Default is %v.", paramName, defaultValue)
//	} else {
//		value = envValue
//		glog.Infof("Env variable %v is %v", paramName, value)
//	}
//	return value
//}
//
//func getEnvBool(paramName string, defaultValue bool) bool {
//	value := defaultValue
//	if envValue := os.Getenv(paramName); envValue == "" {
//		glog.Errorf("Could not get %v env variable. Default is %v.", paramName, defaultValue)
//	} else {
//		value = envValue == "true"
//		glog.Infof("Env variable %v is %v", paramName, value)
//	}
//	return value
//}

//func init(clientSet *kubernetes.Clientset /*config *rest.Config*/) DRManager {
//	glog.Info("Initializing Airflow DR DRManager")
//	//namespace := os.Getenv("CURRENT_NAMESPACE")
//
//	//replicaMap := map[string]int{
//	//	"flower":    getEnvInt("FLOWER_REPLICAS", 1),
//	//	"dagprocessor":    getEnvInt("DAG_PROCESSOR_REPLICAS", 1),
//	//	"worker":    getEnvInt("WORKER_REPLICAS", 1),
//	//	"scheduler": getEnvInt("SCHEDULER_REPLICAS", 1),
//	//	"apiserver": getEnvInt("API_SERVER_REPLICAS", 1),
//	//}
//
//	controller := DRManager{
//		//kubeConfig:            config,
//		namespace:             namespace,
//		startTimeout:          getEnvInt("START_TIMEOUT", 60),
//		shutdownTimeout:       getEnvInt("SHUTDOWN_TIMEOUT", 25),
//		componentToReplicaMap: replicaMap,
//		//statusConfigmapName:   "airflow-dr-state",
//		clientSet: clientSet,
//	}
//	return controller
//}
