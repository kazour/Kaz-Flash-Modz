class com.helperFramework.utils.DebugCaller
{
   function DebugCaller()
   {
   }
   static function getFunctionName(func)
   {
      var _loc2_ = com.helperFramework.utils.DebugCaller._getFunctionNameRecursive(func,_global);
      return _loc2_;
   }
   static function _getFunctionNameRecursive(func, root)
   {
      if(!root)
      {
         return null;
      }
      var _loc3_;
      var _loc6_;
      var _loc7_;
      for(_loc7_ in root)
      {
         if(root[_loc7_] instanceof Function && root[_loc7_].prototype != null)
         {
            for(_loc6_ in root[_loc7_])
            {
               if(root[_loc7_][_loc6_] == func)
               {
                  return _loc7_ + "." + _loc6_;
               }
            }
            _loc3_ = root[_loc7_].prototype;
            _global.ASSetPropFlags(_loc3_,null,8,1);
            for(_loc6_ in _loc3_)
            {
               if(_loc3_[_loc6_] == func)
               {
                  return _loc7_ + "." + _loc6_;
               }
            }
            _global.ASSetPropFlags(_loc3_,null,1,false);
         }
      }
      var _loc5_;
      for(_loc7_ in root)
      {
         if(typeof root[_loc7_] == "object")
         {
            _loc5_ = com.helperFramework.utils.DebugCaller._getFunctionNameRecursive(func,root[_loc7_]);
            if(_loc5_)
            {
               return _loc7_ + "." + _loc5_;
            }
         }
      }
      return null;
   }
}
