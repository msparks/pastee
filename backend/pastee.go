package pastee

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type PasteCreationReq struct {
	Content string
	Mac     string
	Expiry  string
}

type PasteCreationResp struct {
	Id string `json:"id"`
}

type Paste struct {
	content string
	mac     string
	expiry  time.Time
}

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

	// Extract id from URL.
	id := strings.Replace(request.URL.Path, "/pastes/", "", -1)

	fmt.Fprintf(w, "%v", id)
}

func pastesPostHandler(w http.ResponseWriter, request *http.Request) {
	if request.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	const kMaxContentLength = 256 * 1024
	if request.ContentLength > kMaxContentLength {
		w.WriteHeader(http.StatusRequestEntityTooLarge)
		return
	}
	if request.ContentLength < 0 {
		w.WriteHeader(http.StatusLengthRequired)
		return
	}

	postData := make([]byte, request.ContentLength)
	_, err := request.Body.Read(postData)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, "paste must contain a body")
		return
	}

	creationRequest, err := pasteCreationRequestFromPostData(postData)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, "%v\n", err)
		return
	}

	responseBytes, err := json.Marshal(PasteCreationResp{Id: "foo"})
	fmt.Fprintf(w, "request: %+v\n", creationRequest)
	fmt.Fprintf(w, "response: %+v\n", string(responseBytes))
}

func pasteCreationRequestFromPostData(postData []byte) (PasteCreationReq, error) {
	var creationRequest PasteCreationReq
	if err := json.Unmarshal(postData, &creationRequest); err != nil {
		return creationRequest, err
	}
	return creationRequest, nil
}
