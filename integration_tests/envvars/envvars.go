package envvars

import (
	"fmt"
	"os"
)

type EnvVarCfg struct {
	VarName string
	IsCredentials bool
	IsSensitive bool
	ErrMsg string
	DefaultVal string
}

type EnvVars struct {
	envVars map[string]string
}

func NewEnvVars(cfgs []EnvVarCfg) (*EnvVars, error) {
	retval := &EnvVars{
		envVars: make(map[string]string),
	}
	for _, cfg := range cfgs {
		val, ok := os.LookupEnv(cfg.VarName)
		if !ok {
			return nil, fmt.Errorf(fmt.Sprintf("Expected env var was not defined; cfg=%+v", cfg))
		}
		retval.envVars[cfg.VarName] = val
	}

	return retval, nil
}
