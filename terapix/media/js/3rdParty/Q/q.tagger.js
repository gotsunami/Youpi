/*
 * Q.Tagger 0.0.7.3
 *
 * Copyright (c) 2010 Boys Abroad (Wout Fierens)
 *
 * Both commercial and non-commercial domains are allowed to use Q.Tagger under a Creative Commons by-nd License.
 * http://creativecommons.org/licenses/by-nd/3.0/
 */

if(typeof Q=='undefined')
alert("Q is not loaded. Please make sure that your page includes q.js before it includes q.tagger.js");Q.Tagger=Class.create(Q.Base,{initialize:function($super,input,options){$super(input);if(typeof options=="string"&&options.isJSON())
options=options.evalJSON();this.options=$H(this.options).merge({holderStyle:{position:"absolute"}}).merge(options).toObject();Q.addCssFor("tagger");if(!this.input)
alert("Q.Tagger Error: No input was defined to attach the Tagger to!");else if(!this.options.tagList&&!this.options.hiddenTagList)
alert("Q.Tagger Error: No tagList was provided of hiddenTagList defined!");else
this.build();},build:function(){var holder=this.createHolder(this.options.style||'plain'),width=parseInt(this.options.size)||300,input=this.input,self=this,tags,list,item,usedTags;holder.addClassName("q-tagger").setStyle(this.options.holderStyle);list=new Element('ul').addClassName('q-taglist').setStyle({width:width+'px'});tags=this.parseTagList();usedTags=this.strip(this.input.value.split(','));tags.each(function(tag){item=new Element('li').addClassName('q-tag').update(tag);if(usedTags.include(tag))
item.addClassName('q-used');item.observe('click',function(){var used;if(this.hasClassName('q-used')){this.removeClassName('q-used');self.onChange(tag,false);}else{this.addClassName('q-used');self.onChange(tag,true);}
used=list.select('li.q-used').collect(function(used){return used.innerHTML.strip().HTMLdecode();});input.value=used.join(', ');});list.insert(item);});item=new Element('li').addClassName('q-clearer').update('&nbsp;');this.input.observe('keyup',function(){usedTags=self.strip(this.value.split(','));list.select('li').each(function(li){if(usedTags.include(li.innerHTML.strip().HTMLdecode()))
li.addClassName('q-used');else
li.removeClassName('q-used');});});list.insert(item);holder.down("div.q-center").insert(list);},onChange:function(value,used){if(this.options.onChange)
this.options.onChange(value,used,this);},parseTagList:function(){var tags;if(this.options.tagList)
if(typeof this.options.tagList=='string')
if(this.options.tagList.isJSON())
tags=this.options.tagList.parseJSON();else
tags=this.options.tagList.split(',');else
tags=this.options.tagList;else
tags=$(this.options.hiddenTagList).value.split(',');return this.strip(tags);},strip:function(list){return list.collect(function(item){return item.strip();});}});