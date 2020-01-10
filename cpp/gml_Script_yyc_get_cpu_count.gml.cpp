#include "threading.h"
#include <YYGML.h>
#include "gmlids.h"
#ifndef __YYNODEFS
#else
#endif // __YYNODEFS

YYRValue& gml_Script_yyc_get_cpu_count( CInstance* pSelf, CInstance* pOther, YYRValue& _result, int _count,  YYRValue** _args  )
{
YY_STACKTRACE_FUNC_ENTRY( "gml_Script_yyc_get_cpu_count", 0 );
_result = Cpu::getCpuCount();
return _result;
}
