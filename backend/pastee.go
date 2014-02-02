package pastee

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type PastesPostReq struct {
	Content string
	Mac     string
	Expiry  string
}

type PastesPostResp struct {
	Id string `json:"id"`
}

type Paste struct {
	content string
	mac     string
	expiry  time.Time
}

func init() {
	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/pastes/", pastesGetHandler)
	http.HandleFunc("/pastes", pastesPostHandler)
}

func indexHandler(w http.ResponseWriter, request *http.Request) {
	fmt.Fprintf(w, "Index handler")
}

// Handles GET requests to /pastes/{id}.
func pastesGetHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	// Extract id from URL.
	id := strings.Replace(r.URL.Path, "/pastes/", "", -1)

	fmt.Fprintf(w, "%v", id)
}

func pastesPostHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	const kMaxContentLength = 256 * 1024
	if r.ContentLength > kMaxContentLength {
		w.WriteHeader(http.StatusRequestEntityTooLarge)
		return
	}
	if r.ContentLength < 0 {
		w.WriteHeader(http.StatusLengthRequired)
		return
	}

	postData := make([]byte, r.ContentLength)
	_, err := r.Body.Read(postData)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, "POST body required")
		return
	}

	var request PastesPostReq
	err = json.Unmarshal(postData, &request)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, "%v\n", err)
		return
	}

	code, response, _ := pastesPostRPC(&request)
	responseBytes, err := json.Marshal(response)
	w.WriteHeader(code)
	fmt.Fprintf(w, "request: %+v\n", request)
	fmt.Fprintf(w, "response: %+v\n", string(responseBytes))
}

func pastesPostRPC(req *PastesPostReq) (int, PastesPostResp, error) {
	return http.StatusCreated, PastesPostResp{Id: "foo"}, nil
}
