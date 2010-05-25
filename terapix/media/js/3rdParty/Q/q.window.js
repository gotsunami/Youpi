/*
 * Q.Window 0.0.7.3
 *
 * Copyright (c) 2010 Boys Abroad (Wout Fierens)
 *
 * Both commercial and non-commercial domains are allowed to use Q.Window under a Creative Commons by-nd License.
 * http://creativecommons.org/licenses/by-nd/3.0/
 */

if(typeof Q=='undefined')
alert("Q is not loaded. Please make sure that your page includes q.js before it includes q.window.js");Q.Window=Class.create(Q.Base,{initialize:function($super,options){$super();this.persistent=false;if(typeof options=="string"&&options.isJSON())
options=options.evalJSON();this.options=$H(this.options).merge({style:'dark',position:'fixed',draggable:true,closeButton:'right',left:50,top:50,minWidth:300,minHeight:50,maxWidth:3000,maxHeight:3000,hide:false}).merge(options).toObject();if(this.options.position=="static"||this.options.position=="inherit")
this.options.position="relative";Q.addCssFor("window");this.build();},build:function(){var win,close,resize,title,label,background;win=this.holder=new Element("div",{id:this.options.id})
if(this.options.div)
this.div=$(this.options.div);win.addClassName("q-window q-"+this.options.style).setStyle({position:this.options.position,left:parseInt(this.options.left)+"px",top:parseInt(this.options.top)+"px"}).hide();if(this.options.closeButton){close=new Element("div").addClassName("q-window-close");if(this.options.closeButton=='left')
close.addClassName("q-left");close.onclick=(function(){this.hide(true);}).bind(this);win.insert(close);}
background=this.buildBackground(this.options.style);win.insert(background);win.content=new Element("div");background.center.insert(win.content)
win.center=background.center;if(this.options.resizable){resize=new Element("div").addClassName("q-window-resize");win.insert(resize);resize.observe("mousedown",function(event){event.preventDefault?event.preventDefault():event.returnValue=false;resize.resizing=true;})
document.observe("mousemove",(function(event){if(resize.resizing){event.preventDefault?event.preventDefault():event.returnValue=false;var width=event.pointerX()-parseInt(win.getStyle("left"))-8,height=event.pointerY()-parseInt(win.getStyle("top"))-8,offset;if(this.options.position=="fixed"){offset=document.viewport.getScrollOffsets();width-=offset.left;height-=offset.top;}
if(this.validWidth(width))
win.down(".q-content").setStyle({width:width+"px"});if(this.validHeight(height))
win.down(".q-content").setStyle({height:height+"px"});}}).bind(this));document.observe("mouseup",function(){if(resize.resizing)
resize.resizing=false;});}
title=new Element("div").addClassName("q-window-title");win.insert(title);if(this.options.draggable)
new Draggable(win,{handle:title,zindex:100000});title.style.cursor="move";if(this.options.title){label=new Element("p").addClassName("q-window-label").update(this.options.title);title.insert(label);}
this.holder.observe("mouseup",(function(){this.restack();}).bind(this));if(trigger=$(this.options.trigger)){trigger.observe("click",(function(){if(!this.visible())
this.show();}).bind(this));}else if(!this.options.hide){this.show();}
this.div.insert(win);this.initSize(win);this.update(this.options.text);},initSize:function(win){var width=300,height;if(this.options.width)
width=this.options.width;if(this.options.height)
height=this.options.height;if(parseInt(width))
width+="px";else
width="auto";if(parseInt(height))
height+="px";else
height="auto";win.center.setStyle({width:width,height:height,minWidth:this.options.minWidth+"px",minHeight:this.options.minHeight+"px",maxWidth:this.options.maxWidth+"px",maxHeight:this.options.maxHeight+"px"});},update:function(content){this.holder.content.update(new Element("div").setStyle({height:"10px"})).insert(content);return this;},insert:function(content,options){this.holder.content.insert(content,options);return this;},visible:function(){return this.holder.visible();},validWidth:function(value){if(this.options.minWidth&&value<this.options.minWidth)
return false;if(this.options.maxWidth&&value>this.options.maxWidth)
return false;return true;},validHeight:function(value){if(this.options.minHeight&&value<this.options.minHeight)
return false;if(this.options.maxHeight&&value>this.options.maxHeight)
return false;return true;},restack:function(){$("q_wrapper").select("div.q-window").each(function(win){win.style.zIndex=win.hasClassName("q-window-blocking")?99997:99995;});this.holder.style.zIndex=this.holder.hasClassName("q-window-blocking")?99998:99996;},onShow:function(){this.restack();if(typeof this.options.onShow=="function")
this.options.onShow();},onHide:function(){if(typeof this.options.onHide=="function")
this.options.onHide();}});Q.Alert=Class.create(Q.Window,{initialize:function($super,title,message,options){var dim=document.viewport.getDimensions(),next,win,msg,wrapper;options=$H({width:300,minHeight:30,draggable:false,closeButton:false,left:dim.width/2-(options&&options.width?options.width/2:150),top:dim.height/3-75,title:title,confirmLabel:"Ok!"}).merge(options||{}).toObject();$super(options);this.holder.addClassName("q-window-blocking").setStyle({zIndex:99998});this.protection=new Element("div").addClassName("q-protective-layer");this.div.insert({top:this.protection});this.protection.hide();next=new Element("input",{type:"button",value:this.options.confirmLabel}).addClassName("q-button q-next-button");next.onclick=(function(){this.onConfirm();}).bind(this);wrapper=new Element("div").addClassName("q-buttons-wrapper");_QWindowConfirmEvent=(function(event){if(event.keyCode==13)
this.onConfirm(_QWindowConfirmEvent);}).bind(this);Event.observe(document,"keyup",_QWindowConfirmEvent);msg=new Element("p").setStyle({margin:"10px 10px 20px 10px"}).update(message);wrapper.insert(next);this.update(msg).insert(wrapper);if(trigger=$(this.options.trigger)){trigger.observe("click",(function(){this.show();this.protection.appear({duration:0.1,to:0.5});}).bind(this));}else{this.show();this.protection.appear({duration:0.1,to:0.5});}},onConfirm:function(){Event.stopObserving(document,"keyup",_QWindowConfirmEvent);Event.stopObserving(document,"keyup",_QWindowCancelEvent);this.hide();if(typeof this.options.onConfirm=="function")
this.options.onConfirm();this.holder.remove();this.protection.remove();}})
Q.Confirm=Class.create(Q.Alert,{initialize:function($super,title,message,options){var cancel,clearer;options=$H({cancelLabel:"Cancel"}).merge(options||{}).toObject();$super(title,message,options);cancel=new Element("input",{type:"button",value:this.options.cancelLabel}).addClassName("q-button q-cancel-button");cancel.onclick=(function(){this.onCancel();}).bind(this);_QWindowCancelEvent=(function(event){if(event.keyCode==27)
this.onCancel(_QWindowCancelEvent);}).bind(this);Event.observe(document,"keyup",_QWindowCancelEvent);this.holder.down("div.q-buttons-wrapper").insert({top:cancel});if(trigger=$(this.options.trigger)){trigger.observe("click",(function(){this.show();}).bind(this));}else{this.show();}},onCancel:function(){Event.stopObserving(document,"keyup",_QWindowConfirmEvent);Event.stopObserving(document,"keyup",_QWindowCancelEvent);this.hide();if(typeof this.options.onCancel=="function")
this.options.onCancel();this.holder.remove();this.protection.remove();}});Q.Prompt=Class.create(Q.Confirm,{initialize:function($super,title,message,options){$super(title,message,options);this.textarea=new Element("textarea").addClassName("q-textarea").setValue(this.options.text)
this.holder.down("div.q-buttons-wrapper").insert({before:this.textarea});if(trigger=$(this.options.trigger)){trigger.observe("click",(function(){this.show();}).bind(this));}else{this.show();}},onConfirm:function(){Event.stopObserving(document,"keyup",_QWindowConfirmEvent);Event.stopObserving(document,"keyup",_QWindowCancelEvent);this.hide();if(typeof this.options.onConfirm=="function")
this.options.onConfirm(this.textarea.value);this.holder.remove();this.protection.remove();}});var _QWindowCancelEvent,_QWindowConfirmEvent;