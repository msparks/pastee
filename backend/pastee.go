package pastee

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"time"

	"appengine"
	"appengine/datastore"
)

type PastesGetResp struct {
	Content string `json:"content"`
	Mac     string `json:"mac"`
	Expiry  string `json:"expiry"`
}

type PastesPostReq struct {
	Content string
	Mac     string
	Expiry  string
}

type PastesPostResp struct {
	Id string `json:"id"`
}

type Paste struct {
	Content string
	Mac     string
	Expiry  time.Time
}

type ErrorResp struct {
	Error string `json:"error"`
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

	// Extract MBase31 ID from URL.
	mb31IDString := strings.Replace(r.URL.Path, "/pastes/", "", -1)

	// Decode MBase31 ID.
	// The zeroth ID is special and is considered invalid.
	mb31ID, err := MBase31FromString(mb31IDString)
	if err != nil || mb31ID.Value == 0 {
		// All parse result in a 404.
		w.WriteHeader(http.StatusNotFound)
		return
	}

	ctx := appengine.NewContext(r)
	key := datastore.NewKey(ctx, "paste", "", mb31ID.Value, nil)
	var paste Paste
	if err := datastore.Get(ctx, key, &paste); err != nil {
		w.WriteHeader(http.StatusNotFound)
		return
	}

	// Convert Paste to a PasteGetResp.
	response := PastesGetResp{}
	response.Content = paste.Content
	response.Mac = paste.Mac
	response.Expiry = paste.Expiry.Format(time.RFC3339)

	responseBytes, _ := json.Marshal(response)
	fmt.Fprintf(w, "%v\n", string(responseBytes))
}

func pastesPostHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	const kMaxBodyLength = 256 * 1024
	if r.ContentLength > kMaxBodyLength {
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

	ctx := appengine.NewContext(r)
	code, response, err := pastesPostRPC(&ctx, &request)
	w.WriteHeader(code)
	var responseBytes []byte
	if err != nil {
		errorResponse := ErrorResp{Error: err.Error()}
		responseBytes, _ = json.Marshal(errorResponse)
	} else {
		responseBytes, _ = json.Marshal(response)
	}
	fmt.Fprintf(w, "%v\n", string(responseBytes))
}

func pastesPostRPC(ctx *appengine.Context, request *PastesPostReq) (int, PastesPostResp, error) {
	// TODO(ms): These should be configurable.
	const kMaxContentLength = 256 * 1024 // 256 KiB
	const kMaxMacLength = 128
	const kMaxLifetime = 7 * 24 * time.Hour
	const kDefaultLifetime = 1 * time.Hour

	// Length checking.
	if request.Content == "" {
		return http.StatusBadRequest, PastesPostResp{}, errors.New("content is required")
	} else if len(request.Content) > kMaxContentLength {
		return http.StatusBadRequest, PastesPostResp{}, errors.New(
			fmt.Sprintf("max content is %d bytes", kMaxContentLength))
	} else if len(request.Mac) > kMaxMacLength {
		return http.StatusBadRequest, PastesPostResp{}, errors.New(
			fmt.Sprintf("max mac length is %d bytes", kMaxMacLength))
	}

	// Verify MAC looks lke a hex digest.
	if m, _ := regexp.MatchString("^[a-f0-9]*$", request.Mac); !m {
		return http.StatusBadRequest, PastesPostResp{}, errors.New(
			fmt.Sprintf("mac must be a hex digest"))
	}

	// Parse and validate expiration date.
	now := time.Now()
	var expiry time.Time
	if request.Expiry != "" {
		var err error
		expiry, err = time.Parse(time.RFC3339, request.Expiry)
		if err != nil {
			return http.StatusBadRequest, PastesPostResp{}, errors.New("bad time format")
		}

		if expiry.After(now.Add(kMaxLifetime)) {
			return http.StatusBadRequest, PastesPostResp{}, errors.New(
				fmt.Sprintf("maximum lifetime is %v", kMaxLifetime))
		}
	} else {
		expiry = now.Add(kDefaultLifetime)
	}

	// Construct Paste entity for datastore.
	var paste Paste
	paste.Content = request.Content
	paste.Mac = request.Mac
	paste.Expiry = expiry

	// Insert Paste.
	key, err := datastore.Put(
		*ctx, datastore.NewIncompleteKey(*ctx, "paste", nil), &paste)
	if err != nil {
		return http.StatusInternalServerError, PastesPostResp{}, err
	}

	// Paste created successfully.
	var response PastesPostResp
	response.Id = MBase31{Value: key.IntID()}.ToString()
	return http.StatusCreated, response, nil
}
