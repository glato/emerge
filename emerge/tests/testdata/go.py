# Borrowed for testing with real test data from https://github.com/wailsapp/wails

GO_TEST_FILES = {"manager.go": """

package event

import (
	"fmt"
	"sync"

	"github.com/wailsapp/wails/lib/interfaces"
	"github.com/wailsapp/wails/lib/logger"
	"github.com/wailsapp/wails/lib/messages"
)

// Manager handles and processes events
type Manager struct {
	incomingEvents chan *messages.EventData
	quitChannel    chan struct{}
	listeners      map[string][]*eventListener
	running        bool
	log            *logger.CustomLogger
	renderer       interfaces.Renderer // Messages will be dispatched to the frontend
	wg             sync.WaitGroup
	mu             sync.Mutex
}

// NewManager creates a new event manager with a 100 event buffer
func NewManager() interfaces.EventManager {
	return &Manager{
		incomingEvents: make(chan *messages.EventData, 100),
		quitChannel:    make(chan struct{}, 1),
		listeners:      make(map[string][]*eventListener),
		running:        false,
		log:            logger.NewCustomLogger("Events"),
	}
}

// PushEvent places the given event on to the event queue
func (e *Manager) PushEvent(eventData *messages.EventData) {
	e.incomingEvents <- eventData
}

// eventListener holds a callback function which is invoked when
// the event listened for is emitted. It has a counter which indicates
// how the total number of events it is interested in. A value of zero
// means it does not expire (default).
type eventListener struct {
	callback func(...interface{}) // Function to call with emitted event data
	counter  uint                 // Expire after counter callbacks. 0 = infinite
	expired  bool                 // Indicates if the listener has expired
}

// Creates a new event listener from the given callback function
func (e *Manager) addEventListener(eventName string, callback func(...interface{}), counter uint) error {

	// Sanity check inputs
	if callback == nil {
		return fmt.Errorf("nil callback bassed to addEventListener")
	}

	// Create the callback
	listener := &eventListener{
		callback: callback,
		counter:  counter,
	}
	e.mu.Lock()
	// Check event has been registered before
	if e.listeners[eventName] == nil {
		e.listeners[eventName] = []*eventListener{}
	}

	// Register listener
	e.listeners[eventName] = append(e.listeners[eventName], listener)
	e.mu.Unlock()
	// All good mate
	return nil
}

// On adds a listener for the given event
func (e *Manager) On(eventName string, callback func(...interface{})) {
	// Add a persistent eventListener (counter = 0)
	err := e.addEventListener(eventName, callback, 0)
	if err != nil {
		e.log.Error(err.Error())
	}
}
""", "assetserver.go": """
package assetserver

import (
	"bytes"
	"context"
	"fmt"
	iofs "io/fs"
	"net/http"
	"net/http/httptest"
	"strconv"

	"github.com/wailsapp/wails/v2/internal/frontend/runtime"
	"github.com/wailsapp/wails/v2/internal/logger"

	"golang.org/x/net/html"
)

const (
	runtimeJSPath = "/wails/runtime.js"
	ipcJSPath     = "/wails/ipc.js"
)

type AssetServer struct {
	handler   http.Handler
	runtimeJS []byte
	ipcJS     func(*http.Request) []byte

	logger *logger.Logger

	servingFromDisk     bool
	appendSpinnerToBody bool
}

func NewAssetServer(ctx context.Context, vfs iofs.FS, assetsHandler http.Handler, bindingsJSON string) (*AssetServer, error) {
	handler, err := NewAssetHandler(ctx, vfs, assetsHandler)
	if err != nil {
		return nil, err
	}

	return NewAssetServerWithHandler(ctx, handler, bindingsJSON)
}

func NewAssetServerWithHandler(ctx context.Context, handler http.Handler, bindingsJSON string) (*AssetServer, error) {
	var buffer bytes.Buffer
	if bindingsJSON != "" {
		buffer.WriteString(`window.wailsbindings='` + bindingsJSON + `';` + "\n")
	}
	buffer.Write(runtime.RuntimeDesktopJS)

	result := &AssetServer{
		handler:   handler,
		runtimeJS: buffer.Bytes(),

		// Check if we have been given a directory to serve assets from.
		// If so, this means we are in dev mode and are serving assets off disk.
		// We indicate this through the `servingFromDisk` flag to ensure requests
		// aren't cached in dev mode.
		servingFromDisk: ctx.Value("assetdir") != nil,
	}

	if _logger := ctx.Value("logger"); _logger != nil {
		result.logger = _logger.(*logger.Logger)
	}

	return result, nil
}
"""}
