artificialturf
==============

Provides greenlet emulation for Jython using normal threads.

At first glance, this may seem to be of no value. After all, isn't the
point of greenlets is to avoid the overhead of regular threads? But
there are a number of reasons that make this reasonable:

* Experience has shown that one can readily run 1000s or 10000s of
  threads on the JVM using Linux. Close control of stack size
  allocations might make this work for certain cases.

* Lightweight threads are available for the JVM using Quasar. (Such
  lightweight threads, like greenlets, save the callstack to the heap
  when the greenlet is not active.) To really make use of this support
  will require supporting Python bytecode in Jython, given that a call
  to `switch` cannot be reliably statically identified, unlike `yield`
  in normal Python coroutines. Such support in Jython for Python
  bytecode is a feature that is needed for other reasons, including
  support for invokedynamic, so it's reasonable to assume it will be
  delivered at some point.

* Certain codebases are migrating away from greenlet/eventlet, such as
  OpenStack, in favor of externally manage async support, namely
  asyncio.

It's this last point that motivated this development, so that it may
be a bridge to such support for running such interesting codebases on
Jython.
