package main

import (
	"context"
	"fmt"
	"os"

	log "github.com/rchapin/rlog"
	"github.com/rchapin/backup_manager/run"
)

func main() {
	fmt.Println(os.Args)
	ctx, cancel := context.WithCancel(context.Background())
	err := run.Run(os.Args, ctx, cancel)
	if err != nil {
		log.Error(err)
		os.Exit(1)
	}
}
