package main

import (
	"fmt"
	"log"
	"net/http"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(`{"service":"gateway-go","status":"healthy"}`))
	})

	addr := ":8080"
	fmt.Printf("gateway-go listening on %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, r))
}
