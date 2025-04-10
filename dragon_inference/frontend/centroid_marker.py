from mpld3.plugins import PluginBase
from astropy.wcs import WCS
from dragon_analysis import DRAGONAnalysis

class CentroidMarker(PluginBase):
    """ An interactive widget to add points to a MatplotLib Image rendered by mpld3. """
    JAVASCRIPT = """
    const PIXEL_OFFSET_X = 15.7;
    const PIXEL_OFFSET_Y = -15.7;
    
    mpld3.register_plugin("centroid_marker", CentroidMarker);
    CentroidMarker.prototype = Object.create(mpld3.Plugin.prototype);
    CentroidMarker.prototype.constructor = CentroidMarker;
    
    // Constructor method for our CentroidMarker class!
    function CentroidMarker(fig, props) {
        mpld3.Plugin.call(this, fig);
        this.fig = fig;
        
        // Storing the new markers
        this.circles = [];
        this.coordinates = [];
    }
    
    // Function to get the stored coordinates of the circles
    CentroidMarker.prototype.getCoordinates = function() {
        return this.coordinates;
    };
    
    CentroidMarker.prototype.draw = function() {
        var fig = this.fig;
        var self = this;  // Save the `this` context for later use

        fig.canvas.on("click", function() {
            var pos = d3.mouse(this);
            var x = fig.axes[0].x.invert(pos[0]) - PIXEL_OFFSET_X;
            var y = fig.axes[0].y.invert(pos[1]) - PIXEL_OFFSET_Y;
                
            var newCentroid = fig.canvas.append("circle")
                .attr("cx", pos[0])
                .attr("cy", pos[1])
                .attr("r", 3)
                .style("fill", "red");
                
            self.circles.push(newCentroid);
            self.coordinates.push({ x: x, y: y });
            
            console.log("Centroids at" + x + ", " + y);
            // We only want at most 2 centroids
            if (self.circles.length === 2) {
                window.top.stBridges.send("coordinate_data", self.coordinates);
            }
        });
    }
    """

    def __init__(self):
        self.dict_ = {"type": "centroid_marker"}



