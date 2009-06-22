/* Main page display, with file upload and display grid.
 */

$(document).ready(function() {
  // Provide collapsible views of BioSQL records.
  $("#bioentry_records").accordion(
    {collapsible: true, active: false, clearStyle: true});
  // Use Ajax to load details when opened.
  $("h3", "#bioentry_records").click(function(e) {
    var contentDiv = $(this).next("div");
    contentDiv.load($(this).find("a").attr("href"));      
  });    

  // Provide file upload via Ajax. This still needs some work with the hover
  // effects
  var button=$("#button1"), interval;
  //button.click(function() {
  //  console.info('clicked button');
  //});
  new Ajax_upload(button, {
    action: 'genbank_upload',
    name: 'upload_file',
    data: {action: 'genbank_upload'},
    onSubmit: function(file, ext) {
      //button.text('Uploading');
      button.addClass("ui-state-disabled");
      this.disable();
    },
    onComplete: function(file, response) {
      console.info(response);
      //button.text('Upload');
      button.removeClass("ui-state-disabled");
      this.enable();
    }
  });

  /* Hover and click logic for buttons:
   * http://www.filamentgroup.com/lab/
   * styling_buttons_and_toolbars_with_the_jquery_ui_css_framework/
   */
  $(".fg-button:not(.ui-state-disabled)").hover(function(){
      $(this).addClass("ui-state-hover"); 
    },
    function(){ 
      $(this).removeClass("ui-state-hover"); 
    }).mousedown(function(){
      $(this).parents('.fg-buttonset-single:first').find(
        ".fg-button.ui-state-active").removeClass("ui-state-active");
      if($(this).is('.ui-state-active.fg-button-toggleable, .fg-buttonset-multi .ui-state-active')){
        $(this).removeClass("ui-state-active");
      } else {
        $(this).addClass("ui-state-active");
      }	
    }).mouseup(function(){
      if(!$(this).is('.fg-button-toggleable, .fg-buttonset-single .fg-button, .fg-buttonset-multi .fg-button') ){
        $(this).removeClass("ui-state-active");
      }
  });
});
