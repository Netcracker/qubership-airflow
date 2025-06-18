package main

import (
	"github.com/Netcracker/qubership-disaster-recovery-daemon/client"
	drdConfig "github.com/Netcracker/qubership-disaster-recovery-daemon/config"
	"github.com/Netcracker/qubership-disaster-recovery-daemon/controller"
	"github.com/Netcracker/qubership-disaster-recovery-daemon/server"
	"site-manager/pkg/config"
	drManager "site-manager/pkg/disasterrecovery/airflow"

	"log"
)

func main() {
	// Make a DRD config loader
	cfgLoader := drdConfig.GetDefaultEnvConfigLoader()

	// Build a DRD config
	drdCfg, err := drdConfig.NewConfig(cfgLoader)
	if err != nil {
		log.Fatalln(err.Error())
	}

	kubeClient := client.MakeKubeClientSet()

	airflowCfg := config.GetEnvConfig()

	airflowDrManager := drManager.NewDRManager(airflowCfg, kubeClient)

	//Start DRD server with custom health function inside. This func calculates only additional health status
	go server.NewServer(drdCfg).
		WithHealthFunc(airflowDrManager.HealthAirflow, true).
		Run()

	// Start DRD controller with external DR function
	controller.NewController(drdCfg).
		WithFunc(airflowDrManager.ChangeMode).
		Run()
}
