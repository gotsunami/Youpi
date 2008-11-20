// Javascript functions

function switchVisibility(id)
{
	var visibility = document.getElementById(id).style.display;
	if (visibility == "block") {
		document.getElementById(id).style.display = 'none';
	}
	else {
		document.getElementById(id).style.display = 'block';
	}
	document.getElementById("image" + id).src = "/media/themes/" + guistyle + "/img/16x16/visible.gif";
}
