/*
 * Q.Informer 0.0.7.3
 *
 * Copyright (c) 2010 Boys Abroad (Wout Fierens)
 *
 * Both commercial and non-commercial domains are allowed to use Q.Informer under a Creative Commons by-nd License.
 * http://creativecommons.org/licenses/by-nd/3.0/
 */

if(typeof Q=='undefined')
alert("Q is not loaded. Please make sure that your page includes q.js before it includes q.informer.js");Q.Informer=Class.create(Q.Base,{initialize:function($super,options){$super();if(typeof options=="string"&&options.isJSON())
options=options.evalJSON();Q.addCssFor("informer");this.options=$H(this.options).merge({closeButton:'right',life:{plain:10,info:10,notice:7,warning:12,error:"immortal",dark:10},holderStyle:{position:"fixed",right:"10px",top:"10px",width:"250px",zIndex:100001}}).merge(options).toObject();if(!this.div.down("div.q-holder.messages")){var holder=this.holder=new Element("div").addClassName("q-holder messages").setStyle(this.options.holderStyle);this.div.insert(holder);if(Prototype.Browser.MobileSafari){var holder_width=parseInt(this.options.holderStyle.width)||250,holder_top=parseInt(this.options.holderStyle.top)||10,holder_right=parseInt(this.options.holderStyle.right),holder_left=parseInt(this.options.holderStyle.left),screen_width=document.viewport.getWidth(),off=document.viewport.getScrollOffsets(),left;holder.setStyle({position:'absolute',right:'auto'});_QInformerRepositionEvent=function(){off=document.viewport.getScrollOffsets();screen_width=document.viewport.getWidth();if(holder_right==0||holder_right)
left=(screen_width-holder_width-holder_right-off.left)+'px';else if(holder_left==0||holder_left)
left=holder_left+'px';else
left='10px';holder.morph('left:'+left+';top:'+(off.top+10)+'px;',{duration:0.3});}
window.observe('scroll',_QInformerRepositionEvent);}}else{this.holder=this.div.down("div.q-holder.messages");}
$w("plain info notice warning error dark").each((function(type){this[type]=(function(message,life){this.message(type,message,life);}).bind(this);$$("p.q-"+type).each((function(message){var m,life;if(m=message.className.match(/q-life-([\d\.]+)/))
life=parseFloat(m[1]);else if(message.hasClassName("q-immortal"))
life="immortal";this.message(type,message.innerHTML,life);message.remove();}).bind(this));}).bind(this));},messages:function(type,list,life){if(!list)return;if(typeof list=="string"&&list.isJSON())
list=list.evalJSON();list.each((function(message){this.message(type,message,life)}).bind(this));return this;},message:function(type,text,life){var id=type+"_"+text.toMD5(),message,disappear,remove,close;if(!life)
life=this.options.life[type];if($(id)&&$(id).visible()){$(id).pulsate({pulses:3,duration:1});}else{message=new Element("div",{id:id}).addClassName("q-message q-"+type).setStyle({width:"100%",left:"0"}).hide();message.insert(this.buildBackground(type));message.down(".q-center").insert(text);if(this.options.closeButton){close=new Element("div").addClassName("q-message-close");if(this.options.closeButton=='left')
close.addClassName("q-left");message.insert(close);}
Event.observe(message,"click",(function(){this.disappear(message);}).bind(this));this.holder.insert(message);if(life!="immortal")
(this.disappear).bind(this).delay(life,message);this.appear(message);}
return message;},pending:function(message,id){var pending,bar,text;if(!id)
id="pending_"+Math.random().toMD5();if($(id)){pending=$(id);if(!$(id).visible())
this.holder.insert(pending.remove());}else{pending=new Element("div",{id:id}).addClassName("q-message q-plain q-pending").setStyle({width:"100%",left:"0"}).hide();bar=new Element("div").addClassName("q-pending-bar");pending.insert(this.buildBackground("plain"));if(message&&!message.blank()){text=new Element("div").update(message).addClassName("q-text");pending.down(".q-center").insert(text);}
pending.down(".q-center").insert(bar);Event.observe(pending,"click",(function(){this.disappear(pending);}).bind(this));pending.ready=(function(){this.disappear(pending);}).bind(this);}
this.holder.insert(pending);this.appear(pending);return pending;},progress:function(message,id){var progress,bar,indicator,text;if(!id)
id="progress_"+Math.random().toMD5();if($(id)){progress=$(id);if(!$(id).visible())
this.holder.insert(progress.remove());}else{progress=new Element("div",{id:id}).addClassName("q-message q-plain q-progress").setStyle({width:"100%",left:"0"}).hide();indicator=new Element("div").addClassName("q-indicator");bar=new Element("div").addClassName("q-progress-bar").insert(indicator);progress.insert(this.buildBackground("plain"));if(message&&!message.blank()){text=new Element("div").addClassName("q-text");progress.down(".q-center").insert(text);}
progress.down(".q-center").insert(bar);this.holder.insert(progress);Event.observe(progress,"click",(function(){this.disappear(progress);}).bind(this));progress.update=(function(percent,new_message){if(new_message)
message=new_message;if(percent==0||(percent=parseInt(percent))){if(percent>=100){progress.down(".q-indicator").setStyle({width:"0%"});this.disappear(progress);progress.status=0;}else{text.update(message.gsub(/%n/,percent));progress.down(".q-indicator").morph("width: "+percent+"%",{duration:0.1});progress.status=percent;}}}).bind(this);progress.ready=(function(){this.disappear(progress);}).bind(this);progress.update(0);}
this.appear(progress);return progress;},appear:function(message){if(message.visible())
message.pulsate({pulses:3,duration:0.8});else{message.appear({duration:0.2});if(Prototype.Browser.MobileSafari)
_QInformerRepositionEvent();}},disappear:function(message){message=$(message);if(message.visible()){message.slideUp({duration:0.2});message.morph("margin:0;padding:0;width:0;left:100%;",{duration:0.2});var resetStyle=(function(){message.setStyle({width:"100%",left:"0"});}).bind(this);resetStyle.delay(0.25);}},shutUp:function(){this.holder.select(".q-message").each((function(message){this.disappear(message);}).bind(this));return this;},purgeHidden:function(id){this.holder.select(".q-message").each((function(message){if(!message.visible())
message.remove();}).bind(this));}});var _QInformerRepositionEvent;