package utils

import (
	"context"
	"fmt"
	"github.com/golang/glog"
	"github.com/pkg/errors"
	v12 "k8s.io/api/apps/v1"
	"k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/util/retry"
	"time"
)

//func CreateOrUpdateConfigMap(kubeClient kubernetes.Interface, name string, namespace string, status t.SiteManagerStatus) (*v1.ConfigMap, error) {
//	configMap := &v1.ConfigMap{
//		ObjectMeta: metav1.ObjectMeta{
//			Name: name,
//		},
//		Data: map[string]string{
//			"status": status.Status,
//			"mode":   status.Mode,
//		},
//	}
//
//	_, err := kubeClient.CoreV1().ConfigMaps(namespace).Get(context.TODO(), name, metav1.GetOptions{})
//
//	if err == nil {
//		// ConfigMap already exists -> Update
//		configMap, err = kubeClient.CoreV1().ConfigMaps(namespace).Update(context.TODO(), configMap, metav1.UpdateOptions{})
//		if err != nil {
//			return nil, err
//		}
//	} else {
//		// ConfigMap doesn't exists -> Create
//		configMap, err = kubeClient.CoreV1().ConfigMaps(namespace).Create(context.TODO(), configMap, metav1.CreateOptions{})
//		if err != nil {
//			return nil, err
//		}
//	}
//
//	if err != nil {
//		return nil, errors.Wrap(err, fmt.Sprintf("failed to create ConfigMap with name %v", name))
//	}
//	return configMap, nil
//}

func GetConfigMap(kubeClient kubernetes.Interface, name string, namespace string) (*v1.ConfigMap, error) {

	configMap, err := kubeClient.CoreV1().ConfigMaps(namespace).Get(context.TODO(), name, metav1.GetOptions{})

	if err != nil {
		return nil, err
	}

	return configMap, err
}

// return a condition function that indicates whether the given pod is
// currently running
func isPodRunning(c kubernetes.Interface, podName, namespace string) wait.ConditionFunc {
	return func() (bool, error) {
		glog.Info(".") // progress bar!

		pod, err := c.CoreV1().Pods(namespace).Get(context.TODO(), podName, metav1.GetOptions{})
		if err != nil {
			return false, err
		}

		switch pod.Status.Phase {
		case v1.PodRunning:
			return true, nil
		case v1.PodFailed, v1.PodSucceeded:
			return false, errors.New("Pod completed")
		}
		return false, nil
	}
}

// Poll up to timeout seconds for pod to enter running state.
// Returns an error if the pod never enters the running state.
func waitForPodRunning(c kubernetes.Interface, namespace, podName string, timeout time.Duration) error {
	return wait.PollImmediate(time.Second, timeout, isPodRunning(c, podName, namespace))
}

// ListPods Returns the list of currently scheduled or running pods in `namespace` with the given selector
func ListPods(c kubernetes.Interface, namespace, selector string) (*v1.PodList, error) {
	listOptions := metav1.ListOptions{LabelSelector: selector}
	podList, err := c.CoreV1().Pods(namespace).List(context.TODO(), listOptions)

	if err != nil {
		return nil, err
	}
	return podList, nil
}

// WaitForPodBySelectorRunning Wait up to timeout seconds for all pods in 'namespace' with given 'selector' to enter running state.
// Returns an error if no pods are found or not all discovered pods enter running state.
func WaitForPodBySelectorRunning(c kubernetes.Interface, namespace, selector string, timeout int) error {
	podList, err := ListPods(c, namespace, selector)
	if err != nil {
		return err
	}
	if len(podList.Items) == 0 {
		return fmt.Errorf("no pods in %s with selector %s", namespace, selector)
	}

	for _, pod := range podList.Items {
		if err := waitForPodRunning(c, namespace, pod.Name, time.Duration(timeout)*time.Second); err != nil {
			return err
		}
	}
	return nil
}

func GetStatefulSet(c kubernetes.Interface, namespace string, labelName string, labelValue string) (resultStatefulSet v12.StatefulSet, err error) {
	statefulSetClient := c.AppsV1().StatefulSets(namespace)
	labelSelector := fmt.Sprintf("%s=%s", labelName, labelValue)
	statefulSets, err := statefulSetClient.List(context.TODO(), metav1.ListOptions{LabelSelector: labelSelector})

	if err == nil && len(statefulSets.Items) > 0 && statefulSets.Items[0].UID != "" {
		resultStatefulSet = statefulSets.Items[0]
	} else {
		glog.Errorf("Could not get statefulSet with label %s", labelSelector, err)
		err = errors.WithMessagef(err, fmt.Sprintf("Could not get statefulSet with label %s", labelSelector))
	}
	return resultStatefulSet, err
}

func ScaleStatefulSet(c kubernetes.Interface, namespace string, labelName string, labelValue string, replicas int32, ch chan error) {
	statefulSet, err := GetStatefulSet(c, namespace, labelName, labelValue)

	if err == nil {
		statefulSetClient := c.AppsV1().StatefulSets(namespace)

		err = retry.RetryOnConflict(retry.DefaultRetry, func() error {
			// Retrieve the latest version of StatefulSet before attempting update
			// RetryOnConflict uses exponential backoff to avoid exhausting the apiserver
			result, err := statefulSetClient.Get(context.TODO(), statefulSet.Name, metav1.GetOptions{})
			if err != nil {
				glog.Errorf("Failed to get latest version of StatefulSet: %v", err)
			}

			result.Spec.Replicas = int32Ptr(replicas)
			_, updateErr := statefulSetClient.Update(context.TODO(), result, metav1.UpdateOptions{})
			return updateErr
		})
		if err != nil {
			glog.Errorf("Update of statefulSet %s=%s failed: %v", labelName, labelValue, err)
		} else {
			glog.Infof("Updated statefulSet %s=%s replicas to %v", labelName, labelValue, replicas)
		}
	}
	ch <- err
}

func ListDeployments(c kubernetes.Interface, namespace, selector string) (*v12.DeploymentList, error) {
	listOptions := metav1.ListOptions{LabelSelector: selector}
	deploymentsClient := c.AppsV1().Deployments(namespace)
	deploymentsList, err := deploymentsClient.List(context.TODO(), listOptions)
	if err != nil {
		glog.Errorf("Could not list deployments %s, %v", selector, err)
		return nil, err
	}
	return deploymentsList, nil
}

func ListStatefulSets(c kubernetes.Interface, namespace, selector string) (*v12.StatefulSetList, error) {
	listOptions := metav1.ListOptions{LabelSelector: selector}
	statefulSetsClient := c.AppsV1().StatefulSets(namespace)
	statefulSetsList, err := statefulSetsClient.List(context.TODO(), listOptions)
	if err != nil {
		glog.Errorf("Could not list statefulSets %s, %v", selector, err)
		return nil, err
	}
	return statefulSetsList, nil
}

func GetDeployment(c kubernetes.Interface, namespace string, labelName string, labelValue string) (resultDeployment v12.Deployment, err error) {
	deploymentsClient := c.AppsV1().Deployments(namespace)
	labelSelector := fmt.Sprintf("%s=%s", labelName, labelValue)
	deploymentsList, err := deploymentsClient.List(context.TODO(), metav1.ListOptions{LabelSelector: labelSelector})

	if err == nil {
		if len(deploymentsList.Items) > 0 {
			resultDeployment = deploymentsList.Items[0]
		}
	} else {
		glog.Errorf("Could not get deployment with label %s", labelSelector, err)
	}
	return resultDeployment, err
}

func ScaleDeployment(c kubernetes.Interface, namespace string, labelName string, labelValue string, replicas int32, ch chan error) {
	deployment, err := GetDeployment(c, namespace, labelName, labelValue)

	if err == nil {
		deploymentsClient := c.AppsV1().Deployments(namespace)

		err = retry.RetryOnConflict(retry.DefaultRetry, func() error {
			// Retrieve the latest version of Deployment before attempting update
			// RetryOnConflict uses exponential backoff to avoid exhausting the apiserver
			result, err := deploymentsClient.Get(context.TODO(), deployment.Name, metav1.GetOptions{})
			if err != nil {
				glog.Errorf("Failed to get latest version of Deployment: %v", err)
			}

			result.Spec.Replicas = int32Ptr(replicas)
			_, updateErr := deploymentsClient.Update(context.TODO(), result, metav1.UpdateOptions{})
			return updateErr
		})
		if err != nil {
			glog.Errorf("Update of deployment %s=%s failed: %v", labelName, labelValue, err)
		} else {
			glog.Infof("Updated deployment %s=%s replicas to %v", labelName, labelValue, replicas)
		}
	}
	ch <- err
}

func PodRunningAndReady(pod v1.Pod) (bool, error) {
	switch pod.Status.Phase {
	case v1.PodFailed, v1.PodSucceeded:
		return false, fmt.Errorf("pod completed")
	case v1.PodRunning:
		for _, cond := range pod.Status.Conditions {
			if cond.Type != v1.PodReady {
				continue
			}
			return cond.Status == v1.ConditionTrue, nil
		}
		return false, fmt.Errorf("pod ready condition not found")
	}
	return false, nil
}

func int32Ptr(i int32) *int32 { return &i }
