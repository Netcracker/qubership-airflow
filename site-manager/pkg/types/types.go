package types

type AirflowStatus struct {
	Status string `json:"status"`
}

type Config struct {
	ReplicaMap      map[string]int
	StartTimeout    int
	ShutdownTimeout int
	Namespace       string
}
