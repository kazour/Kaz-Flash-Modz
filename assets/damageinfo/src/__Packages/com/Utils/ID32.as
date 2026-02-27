class com.Utils.ID32
{
   var m_Instance;
   var m_Type;
   function ID32()
   {
      this.m_Type = 0;
      this.m_Instance = 0;
      if(arguments.length > 0)
      {
         this.m_Type = arguments[0];
         if(arguments.length > 1)
         {
            this.m_Instance = arguments[1];
         }
      }
   }
   function Equal(other)
   {
      return this.m_Type == other.m_Type && this.m_Instance == other.m_Instance;
   }
   function IsNull()
   {
      return this.m_Type == 0 && this.m_Instance == 0;
   }
   function IsNpc()
   {
      return this.m_Type == _global.Enums.TypeID.e_Type_GC_Character && this.m_Instance < 16777216 && this.m_Instance != 0;
   }
   function IsPlayer()
   {
      return this.m_Type == _global.Enums.TypeID.e_Type_GC_Character && this.m_Instance >= 16777216;
   }
   function IsSimpleDynel()
   {
      return this.m_Type == _global.Enums.TypeID.e_Type_GC_SimpleDynel;
   }
   function IsDestructible()
   {
      return this.m_Type == _global.Enums.TypeID.e_Type_GC_Destructible;
   }
   function toString()
   {
      return "" + this.m_Type + ":" + this.m_Instance;
   }
   function GetType()
   {
      return this.m_Type;
   }
   function GetInstance()
   {
      return this.m_Instance;
   }
   function SetType(type)
   {
      this.m_Type = type;
   }
   function SetInstance(instance)
   {
      this.m_Instance = instance;
   }
}
