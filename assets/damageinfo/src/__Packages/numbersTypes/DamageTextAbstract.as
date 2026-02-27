class numbersTypes.DamageTextAbstract
{
   var _container;
   var _contents;
   var _currentPosition;
   var _font;
   var _id;
   var _numContents;
   var _scale;
   var _ttl;
   static var TYPE_HOSTILE = 1;
   static var TYPE_FRIENDLY = 0;
   var DEFAULT_TITLE_SCALE = 0.7;
   var DEFAULT_TEXT_SCALE = 0.5;
   var _contentScale = 100;
   
   // PHASE1: Static shared DropShadowFilter
   static var SHADOW_FILTER = new flash.filters.DropShadowFilter(4,45,0,100,3,3,40,3,false,false,false);
   
   // PHASE3: Properties needed for pooling
   var hostilityType;
   var TYPE;
   
   function DamageTextAbstract(id)
   {
      this._id = id;
      this._contents = [];
      this._numContents = 0;
      this.hostilityType = 0;
   }
   
   function generate(parentClip, xPos, yPos, htmlFont, title, text, scale)
   {
      if(text == null && title != null)
      {
         text = title;
         title = null;
      }
      this._container = parentClip;
      this._font = htmlFont;
      this._scale = scale;
      this._ttl = this._font.m_WaitOnScreen * 60;
      this._container._x = xPos;
      this._addContent(this._generateContent(DamageTextContent.TYPE_TITLE, title, this.DEFAULT_TITLE_SCALE));
      this._addContent(this._generateContent(DamageTextContent.TYPE_TEXT, text, this.DEFAULT_TEXT_SCALE));
      
      // PHASE1: Use static shared filter
      this._container.filters = [numbersTypes.DamageTextAbstract.SHADOW_FILTER];
   }
   
   // PHASE3: Reset object state for pooling (instead of destroy)
   function reset()
   {
      // Clear contents
      var _loc2_;
      var _loc3_ = this._numContents - 1;
      while(_loc3_ >= 0)
      {
         _loc2_ = this._contents[_loc3_];
         if(_loc2_ != null)
         {
            _loc2_.content.removeMovieClip();
            _loc2_ = null;
         }
         _loc3_ = _loc3_ - 1;
      }
      this._contents = [];
      this._numContents = 0;
      
      // Reset properties
      this._font = null;
      this._scale = 0;
      this._ttl = 0;
      this._contentScale = 100;
      this._currentPosition = null;
      this.hostilityType = 0;
      
      // Clear container reference (will be reassigned on next use)
      this._container = null;
   }
   
   // PHASE3: Destroy now calls reset (for backward compatibility)
   function destroy()
   {
      this.reset();
   }
   
   function set contentScale(value)
   {
      this._contentScale = value;
      var _loc2_ = 0;
      while(_loc2_ < this._numContents)
      {
         this._contents[_loc2_]._xscale = this._contents[_loc2_]._yscale = this._contentScale;
         _loc2_ = _loc2_ + 1;
      }
   }
   
   function updateLife(intervalModifyer)
   {
      this._ttl -= intervalModifyer;
      if(this._ttl <= 0)
      {
         return false;
      }
      return true;
   }
   
   function _addContent(newContent)
   {
      if(newContent == null)
      {
         return undefined;
      }
      this._contents[this._numContents] = newContent;
      this._numContents = this._numContents + 1;
   }
   
   function _getContentByType(type)
   {
      var _loc2_ = 0;
      while(_loc2_ < this._numContents)
      {
         if(this._contents[_loc2_].type == type)
         {
            return this._contents[_loc2_];
         }
         _loc2_ = _loc2_ + 1;
      }
      return null;
   }
   
   function _generateContent(type, content, scaleOffset)
   {
      if(content == undefined || content == null || content == "")
      {
         return null;
      }
      var _loc2_ = new DamageTextContent(type, this._container.attachMovie("DamageText", "damageText" + this._numContents, this._container.getNextHighestDepth()));
      var _loc3_ = new TextFormat();
      _loc3_.color = this._font.m_Color;
      _loc3_.bold = this._font.m_Bold;
      _loc3_.italic = this._font.m_Italic;
      _loc3_.underline = this._font.m_Underline;
      _loc3_.kerning = this._font.m_Kerning;
      _loc2_.label.autoSize = true;
      _loc2_.label.setNewTextFormat(_loc3_);
      _loc2_.label.text = content;
      _loc2_.scale = scaleOffset;
      _loc2_._xscale = _loc2_._yscale = this._scale * scaleOffset;
      _loc2_.label._x = (- _loc2_.label._width) * 0.5;
      _loc2_.label._y = (- _loc2_.label._height) * 0.5;
      return _loc2_;
   }
   
   function _start(target, offsetX, offsetY)
   {
      if(!target)
      {
         return undefined;
      }
      if(!offsetX || offsetX == null || offsetX == undefined)
      {
         offsetX = 0;
      }
      if(!offsetY || offsetY == null || offsetY == undefined)
      {
         offsetY = 0;
      }
      target._x = offsetX;
      target._y = offsetY;
   }
   
   function get contentScale()
   {
      return this._contentScale;
   }
   
   function get id()
   {
      return this._id;
   }
   
   function get ttl()
   {
      return this._ttl;
   }
   
   function get container()
   {
      return this._container;
   }
   
   function get scale()
   {
      return this._scale;
   }
   
   function get currentPosition()
   {
      return this._currentPosition;
   }
}
