class GUIFramework.ClipNode
{
   var SignalLoaded;
   var m_DepthLayer;
   var m_LoadArguments;
   var m_ModalLevel;
   var m_Movie;
   var m_ObjectName;
   var m_StretchToScreen;
   var m_SubDepth;
   function ClipNode(objecName, movie, stretchToScreen, depthLayer, subDepth, loadArguments)
   {
      this.m_ObjectName = objecName;
      this.m_Movie = movie;
      this.m_StretchToScreen = stretchToScreen;
      this.m_DepthLayer = depthLayer;
      this.m_SubDepth = subDepth;
      this.m_ModalLevel = 0;
      this.m_LoadArguments = loadArguments;
      this.SignalLoaded = new com.Utils.Signal();
   }
   function Compare(rhs)
   {
      if(this.m_ModalLevel != rhs.m_ModalLevel)
      {
         return this.m_ModalLevel - rhs.m_ModalLevel;
      }
      if(this.m_DepthLayer != rhs.m_DepthLayer)
      {
         return this.m_DepthLayer - rhs.m_DepthLayer;
      }
      return this.m_SubDepth - rhs.m_SubDepth;
   }
   function toString()
   {
      return this.m_Movie + " Depthlayer: " + this.m_DepthLayer + " SubDepth" + this.m_SubDepth + " Real depth: " + this.m_Movie.getDepth();
   }
}
