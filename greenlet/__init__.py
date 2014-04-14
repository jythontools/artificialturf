# artificialturf - emulation of greenlet using threads

import sys
import threading
from collections import namedtuple
from java.util.concurrent import ArrayBlockingQueue


class error(Exception):
    pass

class GreenletExit(Exception):
    pass


context = threading.local()
ROOT = object()
print "root", ROOT


GreenletArgs = namedtuple("GreenletArgs", ["args", "kwargs"])
GreenletException = namedtuple("GreenletException", ["typ", "val", "tb"])


def getcurrent():
    print "getcurrent: thread local context", context._current
    return context._current


def _handle_result(result, applicable=False):
    if isinstance(result, GreenletArgs):
        if applicable:
            return result.args, result.kwargs
        if result.args and result.kwargs:
            return result.args, result.kwargs
        elif result.args:
            return result.args
        else:
            return result.kwargs
    elif isinstance(result, GreenletException):
        if isinstance(result.typ, GreenletExit):
            return None
        else:
            raise result.typ, result.val, result.tb
    else:
        raise AssertionException("Not valid mailbox result for greenlet")


class greenlet(object):

    def __init__(self, run=None, parent=None):
        self.run = run
        if parent is not None:
            self.parent = parent
        else:
            self.parent = getcurrent()
        self._frame = None

        # Mailbox is used in this code to highlight that it's a specialized
        # queue of length 1, used for the specific synchronization model of
        # greenlet.switch
        self._mailbox = ArrayBlockingQueue(1)

        self._thread = threading.Thread(target=self._wrapper)
        self._thread.daemon = True  # greenlets don't block exit
        self._thread.start()

    def __str__(self):
        return "<greenlet id={}, parent={}, frame={}, mailbox={}, thread={}>".format(
            id(self), id(self.parent) if self.parent else None, self._frame, self._mailbox, self._thread.name)

    def switch(self, *args, **kwargs):
        # Using add ensures that we will quickly fail if multiple greenlets
        # switch to the same one. Should not happen in actual greenlets,
        # and presumably the user-directed scheduling of switch should ensure
        # the same for this emulation
        print "In switch for", self
        if self.parent is ROOT:
            print "Returning from switch to root of tree"
            return
        self._mailbox.add(GreenletArgs(args, kwargs))
        self._frame = sys._getframe(-1)  # caller
        try:
            return _handle_result(context._current._mailbox.take())
        finally:
            self._frame = None

    def throw(self, *args):
        if len(args == 0):
            self._mailbox.add(GreenletException(GreenletExit(), None, None))
        else:
            self._mailbox.add(GreenletException(
                args[0], args[1] if len(args) > 1 else None, args[2]  if len(args) > 2 else None))
        self._frame = sys._getframe(-1)  # caller
        try:
            return _handle_result(context._current._mailbox.take())
        finally:
            self._frame = None

    @property
    def dead(self):
        return not self._thread.is_alive()

    @property
    def gr_frame(self):
        return self._frame

    def __nonzero__(self):
        return self._thread.is_alive() and not hasattr(self, "run")
 
    def _wrapper(self):
        # Now that this thread is started, we need to be prepared to
        # be immediately switched to it on a subsequent scheduling
        # (all user directed of course)
        context._current = self
        args, kwargs = _handle_result(self._mailbox.take(), applicable=True)

        # per the greenlet docs, the run attribute must be deleted
        # once the greenlet starts running
        run = self.run
        del self.run

        if run:
            print "Running greenlet thread {} self={} run={} args={} kwargs={}".format(self._thread.name, self, run, args, kwargs)
            result = run(*args, **kwargs)
            print "Completed greenlet thread {}".format(self._thread.name)

        # Switch up the parent hierarchy
        print "Switching to parent={} result={}".format(self.parent, result)
        if self.parent: # is not None:
            self.parent.switch(result)
        print "BYE"

    def __del__(self):
        self.throw()


# Consider two greenlets, which we will name alice and bob. Some code
# is running in the context of alice, then it calls
# bob.switch(...). This code has a reference to the bob greenlet,
# because of the user-directed and explicit scheduling in the greenlet
# model. But it needs to retrieve the alice context. As we usually do
# in such cases, we model this context with a thread local.

context._current = greenlet(run=None, parent=ROOT)

print "Initialized context greenlet", context._current
