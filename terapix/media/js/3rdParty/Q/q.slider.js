/*
 * Q.Slider 0.0.7.3
 *
 * Copyright (c) 2010 Boys Abroad (Wout Fierens)
 *
 * Both commercial and non-commercial domains are allowed to use Q.Slider under a Creative Commons by-nd License.
 * http://creativecommons.org/licenses/by-nd/3.0/
 */

if(typeof Q=='undefined')
alert("Q is not loaded. Please make sure that your page includes q.js before it includes q.slider.js");Q.Slider=Class.create(Q.Base,{initialize:function($super,input,options){$super(input);if(typeof options=="string"&&options.isJSON())
options=options.evalJSON();this.options=$H(this.options).merge({holderStyle:{position:"absolute"},trackStyle:{backgroundImage:"url("+Q.image_path_h+")",backgroundRepeat:"repeat-x",backgroundPosition:"0 -197px",width:"200px",height:"3px",position:"absolute",left:"15px",top:"22px"},trackStyleVertical:{backgroundImage:"url("+Q.image_path_v+")",backgroundRepeat:"repeat-y",backgroundPosition:"-197px 0",width:"3px",height:"200px",position:"absolute",left:"21px",top:"15px"},handleStyle:{backgroundImage:"url("+Q.image_path_h+")",backgroundRepeat:"no-repeat",backgroundPosition:"0px -168px",width:"24px",height:"24px",position:"relative",marginTop:"-11px",marginLeft:"0px",cursor:"pointer"},handleStyleVertical:{marginTop:"0px",marginLeft:"-11px"}}).merge(options).toObject();if(this.options.format)
this.options.format=this.options.format.match(/^(.*?)([\d]+)(.([\d]+))?(.*?)$/);if(!this.input)
alert("Q.Slider Error: No input was defined to attach the Slider to!");else
this.build();},build:function(){var holder=this.createHolder("plain"),track=new Element("div"),handle=new Element("div"),size=parseInt(this.options.size)||200,options;this.options.trackStyle.width=size+"px";this.options.trackStyleVertical.width=size+"px";holder.addClassName("slider").setStyle(this.options.holderStyle).insert(track);track.addClassName("q-track").insert(handle).setStyle(this.options.trackStyle);handle.addClassName("q-handle").setStyle(this.options.handleStyle);if(this.options.axis=="vertical"){holder.setStyle(this.options.holderStyleVertical);holder.down("div.q-center").setStyle({width:"20px",height:(size+8)+"px"});track.setStyle(this.options.trackStyleVertical);handle.setStyle(this.options.handleStyleVertical);}else{holder.down("div.q-center").setStyle({width:(size+8)+"px",height:"20px"});}
this.input.observe("blur",(function(){this.input.value=this.format(this.options.value);}).bind(this));this.input.observe("keyup",(function(event){if(event.keyCode==13)this.hide();this.options.value=this.input.value;}).bind(this));options=$H(this.options).merge({onChange:this.onChange.bind(this),onSlide:this.onSlide.bind(this)}).toObject();this.control=new Control.Slider(handle,track,options);this.setValue(this.options.value||this.input.value||0);},onChange:function(value){if(value==0||value){this.input.setValue(this.format(value));this.options.value=value;this.positionHolder();if(this.options.onChange)
this.options.onChange(value,this);}},onSlide:function(value){if(value==0||value){this.input.setValue(this.format(value));this.options.value=value;if(this.options.onSlide)
this.options.onSlide(value,this);}},setValue:function(value){if(value==0||parseFloat(value)){this.control.setValue(parseFloat(value));this.input.setValue(this.format(value));this.options.value=value;}},format:function(value){if(m=this.options.format){if(!m[4])
value=parseInt(value);else
value=parseFloat(value).toFixed(m[4].length);return(m[1]||"")+value+(m[5]||"");}else{return value;}}});