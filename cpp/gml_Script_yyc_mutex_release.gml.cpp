#include "threading.h"
#include <YYGML.h>
#include "gmlids.h"
#ifndef __YYNODEFS
#else
#endif // __YYNODEFS

YYRValue& gml_Script_yyc_mutex_release( CInstance* pSelf, CInstance* pOther, YYRValue& _result, int _count,  YYRValue** _args  )
{
YY_STACKTRACE_FUNC_ENTRY( "gml_Script_yyc_mutex_release", 0 );
_result = 0;
Mutex::release(*_args[0]);
return _result;
}
