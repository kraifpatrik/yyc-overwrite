#ifndef __THREADING_H__
#define __THREADING_H__

#include <YYGML.h>
#include "windows.h"

// Use in _threadFunc to unpack arguments from ThreadArgs into variables.
#define UNPACK_ARGS(lpParam) \
	ThreadArgs* threadArgs = (ThreadArgs*) lpParam; \
	CInstance* pSelf = threadArgs->pSelf; \
	CInstance* pOther = threadArgs->pOther; \
	int _count = threadArgs->_count; \
	YYRValue** _args = threadArgs->_args; \
	YYRValue _result;

// Use before every return in threads to free ThreadArgs from memory!
#define FREE_ARGS() \
	delete threadArgs;

struct Cpu
{
	static int getCpuCount()
	{
		SYSTEM_INFO systemInfo;
		GetSystemInfo(&systemInfo);
		return (int) systemInfo.dwNumberOfProcessors;
	}
};

/** Used to pass arguments from script functions into thread functions. */
struct ThreadArgs
{
	/** This is `self` in GML. */
	CInstance* pSelf;

	/** This is `other` in GML. */
	CInstance* pOther;

	/** Number of arguments passed to script. */
	int _count;

	/** Array of arguments passed to script. */
	YYRValue** _args;

	ThreadArgs(CInstance* pSelf, CInstance* pOther)
		: pSelf(pSelf)
		, pOther(pOther)
		, _count(0)
		, _args(nullptr)
	{
	}

	ThreadArgs(CInstance* pSelf, CInstance* pOther, int _count,  YYRValue** _args)
		: pSelf(pSelf)
		, pOther(pOther)
		, _count(_count)
	{
		// Copy array of arguments
		YYRValue** __args = new YYRValue*[_count];
		for (int i = 0; i < _count; ++i)
		{
			__args[i] = new YYRValue(*_args[i]);
		}
		this->_args = __args;
	}

	~ThreadArgs()
	{
		// Delete copied arguments
		for (int i = 0; i < _count; ++i)
		{
			delete _args[i];
		}
		delete[] _args;
	}
};

struct Mutex
{
	static void create(const char* name)
	{
		CreateMutex(NULL, FALSE, TEXT(name));
	}

	static void acquire(const char* name)
	{
		HANDLE hMutex; 
		hMutex = OpenMutex( 
			NULL,
			FALSE,
			TEXT(name));
		WaitForSingleObject( 
			hMutex,
			INFINITE);
		CloseHandle(hMutex);
	}

	static void release(const char* name)
	{
		HANDLE hMutex; 
		hMutex = OpenMutex( 
			NULL,
			FALSE,
			TEXT(name));
		ReleaseMutex(hMutex);
		CloseHandle(hMutex);
	}
};

struct Semaphore
{
	static void create(const char* name, int initial, int max)
	{
		CreateSemaphore( 
			NULL,
			initial,
			max,
			TEXT(name));
	}

	static void acquire(const char* name)
	{
		HANDLE hSemaphore; 
		hSemaphore = OpenSemaphore( 
			SEMAPHORE_ALL_ACCESS,
			FALSE,
			TEXT(name));
		WaitForSingleObject( 
			hSemaphore,
			INFINITE);
		CloseHandle(hSemaphore);
	}

	static void release(const char* name)
	{
		HANDLE hSemaphore;
		hSemaphore = OpenSemaphore( 
			SEMAPHORE_ALL_ACCESS | SEMAPHORE_MODIFY_STATE,
			FALSE,
			TEXT(name));
		ReleaseSemaphore(
			hSemaphore,
			1,
			NULL);
		CloseHandle(hSemaphore);
	}
};

#endif // __THREADING_H__
