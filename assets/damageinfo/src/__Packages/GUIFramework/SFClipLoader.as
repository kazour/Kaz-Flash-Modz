class GUIFramework.SFClipLoader
{
   var m_ClipObjectName;
   static var m_Loader;
   static var m_ClassName = "SFClipLoader";
   static var s_TopLevelClips = [];
   static var s_ModalClips = [];
   function SFClipLoader()
   {
   }
   static function SetupLoader()
   {
      var _loc1_ = new Object();
      _loc1_.onLoadInit = GUIFramework.SFClipLoader.OnLoadInit;
      _loc1_.onLoadComplete = GUIFramework.SFClipLoader.OnLoadComplete;
      _loc1_.onLoadError = GUIFramework.SFClipLoader.OnLoadError;
      GUIFramework.SFClipLoader.m_Loader = new MovieClipLoader();
      GUIFramework.SFClipLoader.m_Loader.addListener(_loc1_);
   }
   static function CreateEmptyMovieClip(name, depthLayer, subDepth)
   {
      var _loc2_ = _root.createEmptyMovieClip(name,_root.getNextHighestDepth());
      GUIFramework.SFClipLoader.AddClip(name,_loc2_,depthLayer,subDepth);
      return _loc2_;
   }
   static function LoadClip(url, objectName, stretchToScreen, depthLayer, subDepth, loadArguments)
   {
      if(GUIFramework.SFClipLoader.m_Loader == undefined)
      {
         GUIFramework.SFClipLoader.SetupLoader();
      }
      var _loc3_ = _root.createEmptyMovieClip(objectName,_root.getNextHighestDepth());
      var _loc2_ = new GUIFramework.ClipNode(objectName,_loc3_,stretchToScreen,depthLayer,subDepth,loadArguments);
      GUIFramework.SFClipLoader.AddClipNode(_loc2_);
      GUIFramework.SFClipLoader.m_Loader.loadClip(url,_loc3_);
      return _loc2_;
   }
   static function AddClip(objectName, clip, depthLayer, subDepth)
   {
      var _loc1_ = new GUIFramework.ClipNode(objectName,clip,false,depthLayer,subDepth,undefined);
      GUIFramework.SFClipLoader.AddClipNode(_loc1_);
      return _loc1_;
   }
   static function UnloadClip(objectName)
   {
      var _loc2_ = _root[objectName];
      if(_loc2_ instanceof MovieClip)
      {
         if(_loc2_.OnUnload != undefined)
         {
            _loc2_.OnUnload();
         }
         GUIFramework.SFClipLoader.m_Loader.unloadClip(objectName);
         _loc2_.removeMovieClip();
         GUIFramework.SFClipLoader.RemoveClipNode(_loc2_);
         GUIFramework.SFClipLoaderBase.ClipUnloaded(objectName);
      }
   }
   static function FindClipByPos(x, y)
   {
      var _loc1_ = GUIFramework.SFClipLoader.s_TopLevelClips.length - 1;
      var _loc2_;
      while(_loc1_ >= 0)
      {
         _loc2_ = GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_].m_Movie;
         if(_loc2_.hitTest(x,y,true,true))
         {
            return _loc1_;
         }
         _loc1_ = _loc1_ - 1;
      }
      return -1;
   }
   static function GetClipIndex(movie)
   {
      var _loc1_ = 0;
      while(_loc1_ < GUIFramework.SFClipLoader.s_TopLevelClips.length)
      {
         if(GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_].m_Movie == movie)
         {
            return _loc1_;
         }
         _loc1_ = _loc1_ + 1;
      }
      return -1;
   }
   static function MoveToFront(index)
   {
      var _loc4_;
      var _loc1_;
      var _loc2_;
      if(index >= 0 && index < GUIFramework.SFClipLoader.s_TopLevelClips.length - 1)
      {
         _loc4_ = GUIFramework.SFClipLoader.s_TopLevelClips[index].m_Movie;
         _loc1_ = index + 1;
         while(_loc1_ < GUIFramework.SFClipLoader.s_TopLevelClips.length && GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_].Compare(GUIFramework.SFClipLoader.s_TopLevelClips[index]) <= 0)
         {
            _loc4_.swapDepths(GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_].m_Movie.getDepth());
            _loc2_ = GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_];
            GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_] = GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_ - 1];
            GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_ - 1] = _loc2_;
            _loc1_ = _loc1_ + 1;
         }
      }
   }
   static function SetClipLayer(index, depthLayer, subDepth)
   {
      var _loc2_;
      if(index >= 0 && index < GUIFramework.SFClipLoader.s_TopLevelClips.length)
      {
         _loc2_ = GUIFramework.SFClipLoader.s_TopLevelClips[index];
         GUIFramework.SFClipLoader.RemoveClipByIndex(index,false);
         _loc2_.m_Movie.swapDepths(_root.getNextHighestDepth());
         _loc2_.m_DepthLayer = depthLayer;
         _loc2_.m_SubDepth = subDepth;
         GUIFramework.SFClipLoader.AddClipNode(_loc2_);
      }
   }
   static function AddClipNode(clipNode)
   {
      var _loc2_ = GUIFramework.SFClipLoader.s_TopLevelClips.length - 1;
      var _loc1_;
      while(_loc2_ >= -1)
      {
         if(_loc2_ == -1 || GUIFramework.SFClipLoader.s_TopLevelClips[_loc2_].Compare(clipNode) <= 0)
         {
            _loc1_ = GUIFramework.SFClipLoader.s_TopLevelClips.length - 1;
            while(_loc1_ > _loc2_)
            {
               clipNode.m_Movie.swapDepths(GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_].m_Movie.getDepth());
               _loc1_ = _loc1_ - 1;
            }
            GUIFramework.SFClipLoader.s_TopLevelClips.splice(_loc2_ + 1,0,clipNode);
            break;
         }
         _loc2_ = _loc2_ - 1;
      }
   }
   static function RemoveClipByIndex(index)
   {
      var _loc4_;
      var _loc3_;
      var _loc2_;
      if(index != -1)
      {
         _loc4_ = true;
         if(arguments.length > 1)
         {
            _loc4_ = arguments[1];
         }
         if(_loc4_)
         {
            _loc3_ = GUIFramework.SFClipLoader.s_TopLevelClips[index];
            if(_loc3_.m_ModalLevel != 0)
            {
               _loc2_ = 0;
               while(_loc2_ < GUIFramework.SFClipLoader.s_ModalClips.length)
               {
                  if(GUIFramework.SFClipLoader.s_ModalClips[_loc2_] == _loc3_.m_Movie)
                  {
                     GUIFramework.SFClipLoader.s_ModalClips.splice(_loc2_,1);
                     break;
                  }
                  _loc2_ = _loc2_ + 1;
               }
            }
         }
         GUIFramework.SFClipLoader.s_TopLevelClips.splice(index,1);
         if(_loc3_.m_ModalLevel != 0 && GUIFramework.SFClipLoader.s_ModalClips.length == 1)
         {
            GUIFramework.SFClipLoader.RemoveModalBlocker();
         }
      }
   }
   static function RemoveClipNode(movie)
   {
      GUIFramework.SFClipLoader.RemoveClipByIndex(GUIFramework.SFClipLoader.GetClipIndex(movie));
   }
   static function OnLoadInit(clip)
   {
      var _loc5_ = GUIFramework.SFClipLoader.s_TopLevelClips[GUIFramework.SFClipLoader.GetClipIndex(clip)];
      clip.m_ClipObjectName = _loc5_.m_ObjectName;
      clip.UnloadClip = function()
      {
         GUIFramework.SFClipLoader.UnloadClip(this.m_ClipObjectName);
      };
      var _loc6_ = clip.ResizeHandler;
      var _loc4_;
      var _loc7_;
      var _loc10_;
      var _loc9_;
      var _loc8_;
      if(_loc6_ == undefined)
      {
         if(_loc5_.m_StretchToScreen)
         {
            _loc4_ = Stage.visibleRect;
            clip._x = _loc4_.x;
            clip._y = _loc4_.y;
            clip._width = _loc4_.width;
            clip._height = _loc4_.height - 30;
         }
      }
      else
      {
         _loc7_ = Number(Stage.height);
         _loc10_ = Number(Stage.width);
         _loc9_ = Number(_root._x);
         _loc8_ = Number(_root._y);
         _loc6_(_loc7_,_loc10_,_loc9_,_loc8_);
      }
   }
   static function OnLoadComplete(movie, status)
   {
      GUIFramework.SFClipLoaderBase.ClipLoaded(targetPath(movie),true);
      var _loc3_ = GUIFramework.SFClipLoader.GetClipIndex(movie);
      var _loc1_;
      if(_loc3_ != -1)
      {
         _loc1_ = GUIFramework.SFClipLoader.s_TopLevelClips[_loc3_];
         if(movie.hasOwnProperty("LoadArgumentsReceived"))
         {
            movie.LoadArgumentsReceived(_loc1_.m_LoadArguments);
         }
         _loc1_.SignalLoaded.Emit(_loc1_,true);
      }
   }
   static function OnLoadError(movie, status)
   {
      trace("onLoadError. Failed loading: " + movie);
      var _loc1_ = GUIFramework.SFClipLoader.GetClipIndex(movie);
      var _loc2_;
      if(_loc1_ != -1)
      {
         _loc2_ = GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_];
         _loc2_.SignalLoaded.Emit(_loc2_,false);
         GUIFramework.SFClipLoader.RemoveClipByIndex(_loc1_);
      }
      GUIFramework.SFClipLoaderBase.ClipLoaded(targetPath(movie),false);
   }
   static function AddModalBlocker()
   {
      var _loc2_ = _root.createEmptyMovieClip("MouseCaptureLayer",_root.getNextHighestDepth());
      _loc2_.onPress = function()
      {
      };
      _loc2_.onRelease = function()
      {
      };
      _loc2_.onMouseDown = function()
      {
      };
      _loc2_.onMouseRelease = function()
      {
      };
      _loc2_.beginFill(0,0);
      _loc2_.moveTo(0,0);
      _loc2_.lineTo(10000,0);
      _loc2_.lineTo(10000,10000);
      _loc2_.lineTo(0,10000);
      _loc2_.endFill();
      var _loc3_ = new GUIFramework.ClipNode("MouseCaptureLayer",_loc2_,false,0,0,undefined);
      _loc3_.m_ModalLevel = 1;
      GUIFramework.SFClipLoader.s_ModalClips.push(_loc2_);
      GUIFramework.SFClipLoader.AddClipNode(_loc3_);
   }
   static function RemoveModalBlocker()
   {
      var _loc1_ = GUIFramework.SFClipLoader.s_ModalClips[0];
      GUIFramework.SFClipLoader.s_ModalClips = [];
      GUIFramework.SFClipLoader.RemoveClipNode(_loc1_);
      _loc1_.removeMovieClip();
   }
   static function MakeClipModal(clip, makeModal)
   {
      var _loc5_ = GUIFramework.SFClipLoader.GetClipIndex(clip);
      var _loc4_;
      var _loc2_;
      if(_loc5_ >= 0 && _loc5_ < GUIFramework.SFClipLoader.s_TopLevelClips.length)
      {
         _loc4_ = GUIFramework.SFClipLoader.s_TopLevelClips[_loc5_];
         if(makeModal)
         {
            if(GUIFramework.SFClipLoader.s_ModalClips.length == 0)
            {
               GUIFramework.SFClipLoader.AddModalBlocker();
            }
            GUIFramework.SFClipLoader.s_ModalClips.push(clip);
            _loc4_.m_ModalLevel = GUIFramework.SFClipLoader.s_ModalClips.length;
         }
         else
         {
            _loc2_ = 0;
            while(_loc2_ < GUIFramework.SFClipLoader.s_ModalClips.length)
            {
               if(GUIFramework.SFClipLoader.s_ModalClips[_loc2_] == clip)
               {
                  GUIFramework.SFClipLoader.s_ModalClips.splice(_loc2_,1);
                  break;
               }
               _loc2_ = _loc2_ + 1;
            }
            _loc4_.m_ModalLevel = 0;
            if(GUIFramework.SFClipLoader.s_ModalClips.length == 1)
            {
               GUIFramework.SFClipLoader.RemoveModalBlocker();
            }
         }
         GUIFramework.SFClipLoader.RemoveClipByIndex(_loc5_,false);
         _loc4_.m_Movie.swapDepths(_root.getNextHighestDepth());
         GUIFramework.SFClipLoader.AddClipNode(_loc4_);
      }
   }
   static function PrintTopLevelClipsDebug()
   {
      var _loc1_ = 0;
      while(_loc1_ < GUIFramework.SFClipLoader.s_TopLevelClips.length)
      {
         trace(_loc1_ + ": " + GUIFramework.SFClipLoader.s_TopLevelClips[_loc1_]);
         _loc1_ = _loc1_ + 1;
      }
   }
}
