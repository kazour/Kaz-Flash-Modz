class numbersManagers.AbstractManager
{
   var _elements;
   var _numElements;
   var _onEmptyCallback;
   
   // PHASE3: Callback to release objects to pool
   var _releaseCallback;

   // CUSTOMIZATION: Animation timing and easing
   static var SHOW_DURATION = 0.2;
   static var FADE_DURATION = 0.2;
   static var EASING_TYPE = 0;  // 0=Quad, 1=Cubic, 2=Quart

   // Easing functions (standard AS2 signature: t=time, b=begin, c=change, d=duration)
   static function easeQuad(t, b, c, d)
   {
      t = t / d;
      return -c * t * (t - 2) + b;
   }

   static function easeCubic(t, b, c, d)
   {
      t = t / d - 1;
      return c * (t * t * t + 1) + b;
   }

   static function easeQuart(t, b, c, d)
   {
      t = t / d - 1;
      return -c * (t * t * t * t - 1) + b;
   }

   static function getEase()
   {
      if(numbersManagers.AbstractManager.EASING_TYPE == 1) return numbersManagers.AbstractManager.easeCubic;
      if(numbersManagers.AbstractManager.EASING_TYPE == 2) return numbersManagers.AbstractManager.easeQuart;
      return numbersManagers.AbstractManager.easeQuad;
   }

   function AbstractManager(onEmptyCallback)
   {
      this._onEmptyCallback = onEmptyCallback;
      this._elements = [];
      this._numElements = 0;
      this._releaseCallback = null;
   }
   
   // PHASE3: Set the callback for releasing objects to pool
   function setReleaseCallback(callback)
   {
      this._releaseCallback = callback;
   }
   
   function addElement(element)
   {
      this._elements[this._numElements] = element;
      this._numElements = this._numElements + 1;
   }
   
   function showElement(element)
   {
      element.container._alpha = 0;
      element.contentScale = element.scale * 0.5;
      var ease = numbersManagers.AbstractManager.getEase();
      var dur = numbersManagers.AbstractManager.SHOW_DURATION;
      com.greensock.TweenLite.to(element.container, dur, {_alpha:100, ease:ease});
      com.greensock.TweenLite.to(element, dur, {contentScale:element.scale, ease:ease});
   }
   
   function update()
   {
   }
   
   function destroy()
   {
      if(!this._elements || this._numElements < 1)
      {
         return undefined;
      }
      
      // PHASE1: Iterate backwards, clear array once
      var _loc2_ = this._numElements - 1;
      while(_loc2_ >= 0)
      {
         // PHASE3: Release to pool instead of destroy
         if(this._releaseCallback != null)
         {
            this._releaseCallback(this._elements[_loc2_]);
         }
         else
         {
            this._elements[_loc2_].destroy();
         }
         _loc2_ = _loc2_ - 1;
      }
      
      this._elements = [];
      this._numElements = 0;
   }
   
   function _checkElementLife(element, intervalModifyer)
   {
      return element.updateLife(intervalModifyer);
   }
   
   function _removeElement(oldNumber, offsetY)
   {
      var ease = numbersManagers.AbstractManager.getEase();
      var dur = numbersManagers.AbstractManager.FADE_DURATION;
      com.greensock.TweenLite.to(oldNumber.container, dur, {_alpha:30, _y:oldNumber.container._y - offsetY, ease:ease, onComplete:com.helperFramework.utils.Relegate.create(this, this._deleteElement, oldNumber)});
      com.greensock.TweenLite.to(oldNumber, dur, {contentScale:oldNumber.scale * 0.7, ease:ease});
      if(this._numElements <= 0)
      {
         this._onEmptyCallback();
      }
   }
   
   function _deleteElement(oldNumber)
   {
      // PHASE3: Release to pool instead of destroy
      if(this._releaseCallback != null)
      {
         this._releaseCallback(oldNumber);
      }
      else
      {
         oldNumber.destroy();
      }
   }
   
   function get numElements()
   {
      return this._numElements;
   }
}
