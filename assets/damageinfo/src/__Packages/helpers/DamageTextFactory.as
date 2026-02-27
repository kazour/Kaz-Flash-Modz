class helpers.DamageTextFactory
{
   function DamageTextFactory()
   {
   }
   static function create(newID, textType, hostiliyType)
   {
      var _loc1_;
      if(textType == helpers.DamageNumberType.STATIC)
      {
         _loc1_ = new numbersTypes.FixedDamageText(newID);
      }
      else
      {
         _loc1_ = new numbersTypes.MovingDamageText(newID);
      }
      _loc1_.hostilityType = hostiliyType;
      return _loc1_;
   }
}
