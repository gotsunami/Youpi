/*****************************************************************************
 *
 * Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/


/*
 * Javascript classes for simple multiline tooltip
 *
 */
function tooltip_findPosX(obj) 
{
	var curleft = 0;
	if (obj.offsetParent) {
		while (obj.offsetParent) {
			curleft += obj.offsetLeft
			obj = obj.offsetParent;
		}
	}
	else if (obj.x)
		curleft += obj.x;

	return curleft;
}

function tooltip_findPosY(obj) 
{
	var curtop = 0;
	if (obj.offsetParent) {
		while (obj.offsetParent) {
			curtop += obj.offsetTop
			obj = obj.offsetParent;
		}
	}
	else if (obj.y)
		curtop += obj.y;

	return curtop;
}

function tooltip_show(tooltipId, parentId, posX, posY)
{
	it = document.getElementById(tooltipId);

	if ((it.style.top == '' || it.style.top == 0) 
		&& (it.style.left == '' || it.style.left == 0)) {
		// need to fixate default size (MSIE problem)
		it.style.width = it.offsetWidth + 'px';
		it.style.height = it.offsetHeight + 'px';

		img = document.getElementById(parentId); 
	
		// if tooltip is too wide, shift left to be within parent 
		if (posX + it.offsetWidth > img.offsetWidth) posX = img.offsetWidth - it.offsetWidth;
		if (posX < 0 ) posX = 0; 

		x = tooltip_findPosX(img) + posX;
		y = tooltip_findPosY(img) + posY;

		it.style.top = y + 'px';
		it.style.left = x + 'px';
	}	
	
	it.style.visibility = 'visible'; 
}

function tooltip_hide(id)
{
	it = document.getElementById(id); 
	it.style.visibility = 'hidden'; 
}
