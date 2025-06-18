package config

import (
	"github.com/golang/glog"
	"os"
	"site-manager/pkg/types"
	"strconv"
)

func GetEnvConfig() types.Config {

	return types.Config{
		ReplicaMap: map[string]int{
			"flower":       getEnvInt("FLOWER_REPLICAS", 1),
			"dagprocessor": getEnvInt("DAG_PROCESSOR_REPLICAS", 1),
			"worker":       getEnvInt("WORKER_REPLICAS", 1),
			"scheduler":    getEnvInt("SCHEDULER_REPLICAS", 1),
			"apiserver":    getEnvInt("API_SERVER_REPLICAS", 1),
			"statsd":       getEnvInt("STATSD_REPLICAS", 1),
		},
		StartTimeout:    getEnvInt("START_TIMEOUT", 60),
		ShutdownTimeout: getEnvInt("SHUTDOWN_TIMEOUT", 25),
		Namespace:       os.Getenv("NAMESPACE"),
	}
}

func getEnvInt(paramName string, defaultValue int) int {
	value := defaultValue
	if envValue, err := strconv.Atoi(os.Getenv(paramName)); err != nil {
		glog.Errorf("Could not get %v env variable. Default is %v.", paramName, defaultValue)
	} else {
		value = envValue
		glog.Infof("Env variable %v is %v", paramName, value)
	}
	return value
}

func getEnvBool(paramName string, defaultValue bool) bool {
	value := defaultValue
	if envValue := os.Getenv(paramName); envValue == "" {
		glog.Errorf("Could not get %v env variable. Default is %v.", paramName, defaultValue)
	} else {
		value = envValue == "true"
		glog.Infof("Env variable %v is %v", paramName, value)
	}
	return value
}
