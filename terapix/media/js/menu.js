/*
 * This function activates a link and disables all 'li' elements that 
 * does not match the li_id
 *
 * All divs whose names start with 'menuitem' are hidden too. Only the 
 * element 'div_on' is visible
 *
 */
function swap_display(li_id, div_on, ul_id, div_prefix) {
	var nodeLink = document.getElementById(li_id);
	var nodeTurnOn  = document.getElementById(div_on);
		
	// Hides all div elements whose id starts with div_prefix
	var itemsToHide = document.getElementsByTagName('div');
	for (var i=0; i < itemsToHide.length; i++) {
		if (itemsToHide[i].hasAttribute('id')) {
			if (itemsToHide[i].getAttribute('id').indexOf(div_prefix) == 0) {
				itemsToHide[i].style.display = 'none';
			}
		}
	}

	// Disables all li elements
	var nodeUL = document.getElementById(ul_id);
	for (var i=0; i < nodeUL.childNodes.length; i++) {
		nodeUL.childNodes[i].className = 'disabled';
	}

	// Enables selected li
	nodeLink.parentNode.className = 'enabled';

	// Then show the div block
	nodeTurnOn.style.display = 'block';
	nodeTurnOn.focus();
}
