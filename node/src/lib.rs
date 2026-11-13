//! mb3d-rs as a Node.js add-on: the requests of `mb3d serve` (mb3d-rs:
//! docs/API.md) without the program.  A session keeps the scenes its
//! requests open; a request runs on one of Node's worker threads and its
//! answer comes back as a promise.  `js/mb3d.mjs` is the module people use.

use engine::{api, json, serve::Server};
use napi::bindgen_prelude::AsyncTask;
use napi::threadsafe_function::{ThreadsafeFunction, ThreadsafeFunctionCallMode};
use napi::{Env, Error, Result, Status, Task};
use napi_derive::napi;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

/// Told every line that comes before a request's answer (progress), as JSON.
type Event = ThreadsafeFunction<String, (), String, Status, false>;

#[derive(Default)]
struct Inner {
    server: Mutex<Server>,
    /// counts the calls of `cancel`
    cancels: AtomicU64,
}

#[napi]
#[derive(Default)]
pub struct Session {
    inner: Arc<Inner>,
}

pub struct Request {
    inner: Arc<Inner>,
    request: String,
    event: Option<Event>,
    /// the cancels when the request was made: one more stops it
    cancels: u64,
}

impl Task for Request {
    type Output = String;
    type JsValue = String;

    fn compute(&mut self) -> Result<String> {
        let answer = catch_unwind(AssertUnwindSafe(|| {
            let request = json::parse(&self.request)?;
            let emit = |line: json::Value| {
                if let Some(event) = &self.event {
                    event.call(line.to_json(), ThreadsafeFunctionCallMode::NonBlocking);
                }
            };
            let cancelled = || self.inner.cancels.load(Ordering::SeqCst) != self.cancels;
            // (a request that panicked leaves the scenes as they were: go on)
            let mut server = self.inner.server.lock().unwrap_or_else(|e| e.into_inner());
            Ok::<String, String>(server.handle(&request, &emit, &cancelled).to_json())
        }));
        match answer {
            Ok(Ok(text)) => Ok(text),
            Ok(Err(e)) => Err(Error::from_reason(e)),
            Err(_) => Err(Error::from_reason("the engine failed unexpectedly (a bug in mb3d)")),
        }
    }

    fn resolve(&mut self, _: Env, output: String) -> Result<String> {
        Ok(output)
    }
}

#[napi]
impl Session {
    #[napi(constructor)]
    pub fn new() -> Self {
        Session::default()
    }

    /// One request of `mb3d serve` as JSON; the answer as JSON.  Requests
    /// are carried out one at a time.
    #[napi]
    pub fn request(&self, request: String, event: Option<Event>) -> AsyncTask<Request> {
        AsyncTask::new(Request { inner: self.inner.clone(), request, event, cancels: self.inner.cancels.load(Ordering::SeqCst) })
    }

    /// Stops the renders asked for so far: they answer "cancelled".
    #[napi]
    pub fn cancel(&self) {
        self.inner.cancels.fetch_add(1, Ordering::SeqCst);
    }
}

/// A further folder with formula files (.m3f).
#[napi]
pub fn add_formula_folder(dir: String) {
    api::add_formula_folder(Path::new(&dir));
}

/// A further folder with map pictures.
#[napi]
pub fn add_map_folder(dir: String) {
    api::add_map_folder(Path::new(&dir));
}

/// To call before the program ends when the graphics card was used: waits
/// until no formula is being compiled for the card any more.
#[napi]
pub fn finish() {
    api::finish();
}
