// KzCastbarsPreview.as - Preview Mode & Overlay Management for KzCastbars
// Loosely coupled helper class - only knows about generic bar objects
// Overlay created on rootClip (sibling of bar) so it stays visible when bar hides
class KzCastbarsPreview {
    private var rootClip:MovieClip;
    private var overlayDepth:Number;

    public function KzCastbarsPreview(root:MovieClip) {
        rootClip = root;
        overlayDepth = 9000; // High depth for overlays
    }

    /**
     * Create a draggable preview overlay for a bar.
     * Overlay is created on rootClip (not as child of bar) so it stays visible
     * when bar hides during cast end.
     * @param bar Object with: mc (MovieClip), label (String), overlayColor (Number), width (Number), height (Number)
     */
    public function createOverlay(bar:Object):Void {
        var mc:MovieClip = bar.mc;
        var label:String = bar.label;
        var col:Number = bar.overlayColor;
        var w:Number = bar.width;
        var h:Number = bar.height;

        // Remove existing overlay if any
        if (bar.overlay != null) bar.overlay.removeMovieClip();

        // Create overlay on rootClip (sibling of bar, not child)
        var ovName:String = "_cbOverlay_" + label;
        var ov:MovieClip = rootClip.createEmptyMovieClip(ovName, overlayDepth);
        overlayDepth++;

        // Position at bar location
        ov._x = mc._x;
        ov._y = mc._y;

        // Border + Fill (matches KzGrids style)
        ov.lineStyle(2, 0xFFFFFF, 80);
        ov.beginFill(col, 20);
        ov.moveTo(-2, -2);
        ov.lineTo(w + 2, -2);
        ov.lineTo(w + 2, h + 2);
        ov.lineTo(-2, h + 2);
        ov.lineTo(-2, -2);
        ov.endFill();

        // Single line centered: "Player X:123 Y:456" (label white, coords yellow)
        var infoTF:TextField = ov.createTextField("info", ov.getNextHighestDepth(), 0, 0, w, 18);
        infoTF.selectable = false;
        infoTF.embedFonts = false;
        infoTF.html = true;
        infoTF.htmlText = "<font face='Arial' size='14' color='#FFFFFF'><b>" + label + "</b></font> <font face='Arial' size='11' color='#FFFF00'><b>X:" + Math.round(mc._x) + " Y:" + Math.round(mc._y) + "</b></font>";
        var fmt:TextFormat = new TextFormat();
        fmt.align = "center";
        infoTF.setTextFormat(fmt);

        // Center vertically
        infoTF._y = (h - infoTF.textHeight) / 2 - 2;

        // Store references
        bar.overlay = ov;
        bar.coordsTF = infoTF;
        bar.label = label;

        // Dragging setup
        var self:KzCastbarsPreview = this;
        ov._mc = mc;
        ov._bar = bar;
        ov._self = self;
        ov._w = w;
        ov._h = h;
        ov.useHandCursor = true;

        ov.onPress = function() {
            var maxX:Number = Stage.width - this._w;
            var maxY:Number = Stage.height - this._h;
            // Drag the overlay, sync bar position in onMouseMove
            this.startDrag(false, 0, 0, maxX, maxY);
            this.onMouseMove = function() {
                // Sync bar position to overlay
                this._mc._x = this._x;
                this._mc._y = this._y;
                this._self.updCoords(this._bar);
            };
        };

        ov.onRelease = ov.onReleaseOutside = function() {
            this.stopDrag();
            delete this.onMouseMove;
            // Final sync
            this._mc._x = this._x;
            this._mc._y = this._y;
            this._self.updCoords(this._bar);
        };
    }

    public function updCoords(bar:Object):Void {
        if (bar.coordsTF == null || bar.overlay == null) return;
        bar.coordsTF.htmlText = "<font face='Arial' size='14' color='#FFFFFF'><b>" + bar.label + "</b></font> <font face='Arial' size='11' color='#FFFF00'><b>X:" + Math.round(bar.overlay._x) + " Y:" + Math.round(bar.overlay._y) + "</b></font>";
        var fmt:TextFormat = new TextFormat();
        fmt.align = "center";
        bar.coordsTF.setTextFormat(fmt);
    }

    public function removeOverlay(bar:Object):Void {
        if (bar.overlay != null) {
            bar.overlay.removeMovieClip();
            bar.overlay = null;
        }
        bar.coordsTF = null;
    }
}
