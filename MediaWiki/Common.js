// Fancy diffs
var fancyDiffs = {
	isBigDiff: false,
	isBigDiffThreshold: 72,
	toggle: function(element) {
		var expanded = element.hasClass('diff-expanded');
		var contents = element.parent().children('.diff-contents');
		if(expanded) { // Just collapse then
			element.removeClass('diff-expanded');
			if(fancyDiffs.isBigDiff) {
				contents.hide();
			} else {
				contents.slideUp('fast');
			}
		} else if(element.hasClass('diff-data-loaded')) { // Stuff is already loaded, expand
			element.addClass('diff-expanded');
			contents.slideDown('fast');
		} else if(!element.hasClass('diff-data-requested')) { // Stuff is not loaded
			element.addClass('diff-data-requested');
			var fileName = element.find('span').text().replace(/^\s+|\s+$/g);
			var patchName = element.closest('.diffname');
			var diffName = wgPageName;
			if(patchName && patchName.length && patchName.attr('class')) {
				diffName = patchName.attr('class').substr(9);
			}
			$.get('/?title=Template:PatchDiff/' + encodeURIComponent(diffName.replace(/^Template:PatchDiff\//, '')) + '/' + encodeURIComponent(fileName) + '&action=raw', function(data) {
				contents.html(data);
				if(fancyDiffs.isBigDiff) {
					contents.show();
				} else {
					contents.slideDown('fast');
				}
				element.removeClass('diff-data-requested').addClass('diff-data-loaded').addClass('diff-expanded');
			});
		}
		
	},
	init: function() {
		var diffText = $('.diff-name-text');
		if(diffText.length) {
			// Preload leetle gif
			$('body').append($('<img/>').attr('src', '/images/4/43/Patch_diff_loading.gif').css('display', 'none'));
			diffText.find('span').each(function() {
				$(this).text($(this).find('a').text().replace(/^\s+|\s+$/g));
			});
			diffText.click(function() {
				fancyDiffs.toggle($(this));
				return false;
			});
			fancyDiffs.isBigDiff = $('.diff-file').length > fancyDiffs.isBigDiffThreshold;
		}
	}
};
$(fancyDiffs.init);

// End fancy diffs