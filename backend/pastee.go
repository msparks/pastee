package pastee

import (
	"fmt"
	"net/http"
)

func init() {
	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/pastes", pastesPostHandler)
	http.HandleFunc("/pastes/", pastesGetHandler)
}

func indexHandler(w http.ResponseWriter, request *http.Request) {
	fmt.Fprintf(w, "Index handler")
}

// Handles GET requests to /pastes/{id}.
func pastesGetHandler(w http.ResponseWriter, request *http.Request) {
	if request.Method != "GET" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	fmt.Fprintf(w, "%v", request.URL)
}

func pastesPostHandler(w http.ResponseWriter, request *http.Request) {
	if request.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
}
