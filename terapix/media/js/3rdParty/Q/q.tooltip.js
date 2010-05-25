/*
 * Q.Tooltip 0.0.7.3
 *
 * Copyright (c) 2010 Boys Abroad (Wout Fierens)
 *
 * Both commercial and non-commercial domains are allowed to use Q.Tooltip under a Creative Commons by-nd License.
 * http://creativecommons.org/licenses/by-nd/3.0/
 */

if(typeof Q=='undefined')
alert("Q is not loaded. Please make sure that your page includes q.js before it includes q.tooltip.js");Q.Tooltip=Class.create(Q.Base,{initialize:function($super,options){var unique_id="q_tooltip_"+Math.random().toMD5(),key;$super();if(typeof options=="string"&&options.isJSON())
options=options.evalJSON();this.options=$H(this.options).merge({klass:".q-tip",style:"dark",left:20,top:20,width:200,delay:0.5}).merge(options).toObject();Q.addCssFor("tooltip");this.active=false;this.titles={};this.holder_width=this.options.width+26;this.available_width=this.div.getWidth();document.observe("resize:end",(function(){this.available_width=this.div.getWidth();}).bind(this));this.build();$$(this.options.klass).each((function(element,i){var title=element.title||"";if(element.id.blank()){key=unique_id+"_"+i;element.id=key;}else{key=element.id;}
title.scan(/!(([^ ]+)\.(jpg|jpeg|png|gif|JPG|JPEG|PNG|GIF))!/,function(m){title=title.replace(m[0],'<img src="'+m[1]+'" alt="'+m[2]+'" />');});title=title.gsub(/(\n|\r)/,'<br/>');this.titles[key]=title;element.removeAttribute("title");element.observe("mouseover",(function(event){this.show(element,event);}).bind(this));element.observe("mouseout",(function(){this.hide();}).bind(this));}).bind(this));},build:function(){var holder=this.holder=new Element("div"),background=this.buildBackground(this.options.style);background.insert(new Element("div").addClassName("q-tooltip-center").setStyle({maxWidth:this.options.width+"px"}));holder.addClassName("q-tooltip q-"+this.options.style).insert(background).hide();this.div.insert(holder);},show:function(element,event){var position=event.pointer(),new_pos;new_pos={left:position.x+this.options.left,top:position.y+this.options.top}
if(this.available_width<new_pos.left+this.holder_width)
new_pos.left=this.available_width-this.holder_width;if(!this.holder.visible()&&!this.titles[element.id].blank())
this.holder.setStyle({left:new_pos.left+"px",top:new_pos.top+"px"}).appear({duration:0.2,delay:this.options.delay,queue:{position:"end",limit:2,scope:"q_tooltip"}}).down(".q-tooltip-center").update(this.titles[element.id]);},hide:function(){var queue=Effect.Queues.get("q_tooltip");queue.each(function(effect){effect.cancel();});this.holder.hide();}});