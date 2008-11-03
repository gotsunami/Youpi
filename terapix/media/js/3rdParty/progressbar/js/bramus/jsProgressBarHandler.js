/*****************************************************************
 *
 * jsProgressBarHandler 0.2.1 - by Bramus! - http://www.bram.us/
 *
 * v 0.2.1 - 2007.12.20 - ADD: option : set boxImage
 *                        ADD: option : set barImage (one or more)
 *                        ADD: option : showText
 * v 0.2   - 2007.12.13 - SYS: rewrite in 2 classs including optimisations
 *                        ADD: Config options
 * v 0.1   - 2007.08.02 - initial release
 *
 * @see http://www.barenakedapp.com/the-design/displaying-percentages on how to create a progressBar Background Image!
 *
 * Licensed under the Creative Commons Attribution 2.5 License - http://creativecommons.org/licenses/by/2.5/
 *
 *****************************************************************/
 
		
 /**
  * CONFIG
  * -------------------------------------------------------------
  */
  
 	// Should jsProgressBarHandler hook itself to all span.progressBar elements? - default : true
		var autoHook	= true;		
 
 	// Default Options
		var defaultOptions = {
			animate		: true,										// Animate the progress? - default: true
			showText	: true,										// show text with percentage in next to the progressbar? - default : true
			width		: 120,										// Width of the progressbar - don't forget to adjust your image too!!!
			boxImage	: '/media/js/3rdParty/progressbar/images/bramus/percentImage.png',			// boxImage : image around the progress bar
			barImage	: '/media/js/3rdParty/progressbar/images/bramus/percentImage_back2.png',	// Image to use in the progressbar. Can be an array of images too.
			height		: 12										// Height of the progressbar - don't forget to adjust your image too!!!
		}
		
 /**
  * NO NEED TO CHANGE ANYTHING BENEATH THIS LINE
  * -------------------------------------------------------------
  */
 
	/**
	 * JS_BRAMUS Object
	 * -------------------------------------------------------------
	 */
	 
		if (!JS_BRAMUS) { var JS_BRAMUS = new Object(); }


	/**
	 * ProgressBar Class
	 * -------------------------------------------------------------
	 */
	 
		JS_BRAMUS.jsProgressBar = Class.create();
	
		JS_BRAMUS.jsProgressBar.prototype = {
			
			
			/**
			 * Datamembers
			 * -------------------------------------------------------------
			 */
				el				: null,								// Element where to render the progressBar in
				id				: null,								// Unique ID of the progressbar
				percentage		: null,								// Percentage of the progressbar
				
				options			: null,								// The options
				
				initialPos		: null,								// Initial postion of the background in the progressbar
				pxPerPercent	: null,								// Number of pixels per 1 percent
				
				backIndex		: null,								// index in the array of background images currently used
			
			
			/**
			 * Constructor
			 *
			 * @param HTMLElement el
			 * @param string id
			 * @param int percentage
			 * @return void
			 * -------------------------------------------------------------
			 */
				initialize		: function(el, percentage, options) {
					
					// get the options
					this.options			= Object.clone(defaultOptions);
					Object.extend(this.options, options || {});
					
					// datamembers from arguments
					this.el				= el;
					this.id				= el.id;
					this.percentage		= 0;							// Set to 0 intially, we'll change this later.
					this.backIndex		= 0;							// Set to 0 initially					
									
					// datamembers which are calculatef
					this.imgWidth		= this.options.width * 2;		// define the width of the image (twice the width of the progressbar)
					this.initialPos		= this.options.width * (-1);	// Initial postion of the background in the progressbar (0% is the middle of our image!)
					this.pxPerPercent	= this.options.width / 100;		// Define how much pixels go into 1%
					
					// enfore backimage array
					if (this.options.barImage.constructor.toString().indexOf("Array") == -1) {
						this.options.barImage = Array(this.options.barImage);
					}
					
					// create the progressBar
					this.el.update(
						'<img id="' + this.id + '_percentImage" src="' + this.options.boxImage + '" alt="0%" style="width: ' + this.options.width + 'px; height: ' + this.options.height + 'px; background-position: ' + this.initialPos + 'px 50%; background-image: url(' + this.options.barImage[this.backIndex] + '); padding: 0; margin: 0;"/>' + 
						((this.options.showText == true)?'<span id="' + this.id + '_percentText">0%</span>':''));
				
					// set initial percentage
					this.setPercentage(percentage);
					
				},
			
			
			/**
			 * Sets the percentage of the progressbar
			 *
			 * @param string targetPercentage
			 * @return void
			 * -------------------------------------------------------------
			 */
				setPercentage	: function(targetPercentage) {
	
					// get the current percentage
					var curPercentage	= this.percentage;
					
					// define the new percentage
					if ((targetPercentage.toString().substring(0,1) == "+") || (targetPercentage.toString().substring(0,1) == "-")) {
						targetPercentage	= curPercentage + parseInt(targetPercentage);
					}
				
					// min and max percentages
					if (targetPercentage < 0)		targetPercentage = 0;
					if (targetPercentage > 100)		targetPercentage = 100;
					
					// if we don't need to animate, just change the background position right now and return
					if (this.options.animate == false) {
						this._setBgPosition(targetPercentage);
						return;
					}
					
					// define if we need to add/subtract something to the current percentage in order to reach the target percentage
					if (targetPercentage != curPercentage) {					
						if (curPercentage < targetPercentage) {
							newPercentage = curPercentage + 1;
						} else {
							newPercentage = curPercentage - 1;	
						}			
					} else {
						newPercentage = curPercentage;	
					}
					
					// Change the background position
					this._setBgPosition(newPercentage);
					
					// Do we need to adjust it a wee bit more?
					if (curPercentage != newPercentage) {
						setTimeout(function() { this.setPercentage(targetPercentage); }.bind(this), 10);
					}
					
				},
			
			
			/**
			 * Gets the percentage of the progressbar
			 *
			 * @return int
			 */
				getPercentage		: function(id) {
					return this.percentage;
				},
			
			
			/**
			 * Set the background position
			 *
			 * @param int percentage
			 */
				_setBgPosition		: function(percentage) {
					// adjust the background position
						$(this.id + "_percentImage").style.backgroundPosition 	= "" + (this.initialPos + (percentage * this.pxPerPercent)) + "px 50%";
												
					// adjust the background image and backIndex
						var newBackIndex										= Math.floor((percentage-1) / (100/this.options.barImage.length));
						
						if ((newBackIndex != this.backIndex) && (this.options.barImage[newBackIndex] != undefined)) {
							$(this.id + "_percentImage").style.backgroundImage 	= "url(" + this.options.barImage[newBackIndex] + ")";
						}
						
						this.backIndex											= newBackIndex;
					
					// Adjust the alt & title of the image
						$(this.id + "_percentImage").alt 						= "" + percentage + "%";
						$(this.id + "_percentImage").title 						= "" + percentage + "%";
						
					// Update the text
						if (this.options.showText == true) {
							$(this.id + "_percentText").update("" + percentage + "%");
						}
						
					// adjust datamember to stock the percentage
						this.percentage	= percentage;
				}
		}


	/**
	 * ProgressHandlerBar Class - automatically create ProgressBar instances
	 * -------------------------------------------------------------
	 */
	 
		JS_BRAMUS.jsProgressBarHandler = Class.create();
	
		JS_BRAMUS.jsProgressBarHandler.prototype = {
			
			
			/**
			 * Datamembers
			 * -------------------------------------------------------------
			 */
			 
				pbArray				: new Array(),		// Array of progressBars
		
		
			/**
			 * Constructor
			 *
			 * @return void
			 * -------------------------------------------------------------
			 */
			 
				initialize			: function() {		
				
					// get all span.progressBar elements
					$$('span.progressBar').each(function(el) {
														 
						// create a progressBar for each element
						this.pbArray[el.id]	= new JS_BRAMUS.jsProgressBar(el, parseInt(el.innerHTML.replace("%",""))); 
					
					}.bind(this));
				},
		
		
			/**
			 * Set the percentage of a progressbar
			 *
			 * @param string el
			 * @param string percentage
			 * @return void
			 * -------------------------------------------------------------
			 */
				setPercentage		: function(el, percentage) {
					this.pbArray[el].setPercentage(percentage);
				},
		
		
			/**
			 * Get the percentage of a progressbar
			 *
			 * @param string el
			 * @return int percentage
			 * -------------------------------------------------------------
			 */
				getPercentage		: function(el) {
					return this.pbArray[el].getPercentage();
				}
			
		}


	/**
	 * ProgressHandlerBar Class - hook me or not?
	 * -------------------------------------------------------------
	 */
	
		if (autoHook == true) {
			function initProgressBarHandler() { myJsProgressBarHandler = new JS_BRAMUS.jsProgressBarHandler(); }
			Event.observe(window, 'load', initProgressBarHandler, false);
		}
