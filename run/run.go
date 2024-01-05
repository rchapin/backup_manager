package run

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/akamensky/argparse"
)

const service = "backup_manager"

func Run(args []string, ctx context.Context, cancel context.CancelFunc) error {
	slog.Info("Starting backup_manager", slog.String("args", fmt.Sprintf("%+v", args)))

	parser := argparse.NewParser(service, "Manages rsyncing data from one host to another")
	cfgPath := parser.String("c", "config", &argparse.Options{
		Default:  "/etc/backup_manager/backup_manager.yaml",
		Required: false,
		Help:     "Fully qualified path to the backup_manager config file",
	})
	print(cfgPath)
	// log.Info(parser)

	err := parser.Parse(args)
	if err != nil {
		// log.Critical("Unable to load config file; cftPath=%s", cfgPath)
		panic(err)
	}

	// Start up the rest of the program

	return nil
}
