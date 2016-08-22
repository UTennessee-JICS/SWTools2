<?php
/*
Template Name: Software Request
*/
?>
<script type="text/javascript">
// Validation Function
function validate(registration) {
	if (registration.fullname.value.length < 1)
	{
		alert("Please enter your name.");
		registration.fullname.focus();
		return false;
	}
	if (registration.email.value.length < 1)
	{
		alert("Please enter an email address.");
		registration.email.focus();
		return false;
	}
		if (registration.project.value.length < 1)
	{
		alert("Please enter your INCITE project ID number.");
		registration.project.focus();
		return false;
	}
		if (registration.software.value.length < 1)
	{
		alert("Please enter the software name.");
		registration.software.focus();
		return false;
	}
    
		if (registration.description.value.length < 1)
	{
		alert("Please enter a description of the software.");
		registration.description.focus();
		return false;
	}
    
		if (registration.obtaining.value.length < 1)
	{
		alert("Please enter information about obtaining this software.");
		registration.obtaining.focus();
		return false;
	}
	
		if (registration.justification.value.length < 1)
	{
		alert("Please enter information regarding why this software is needed.");
		registration.justification.focus();
		return false;
	}
   
    
		if (registration.users.value.length < 1)
	{
		alert("Please enter information regarding who will be using this software.");
		registration.users.focus();
		return false;
	}
    
    var boxes = document.getElementsByName('events[]'); // get all the elements named 'events[]'
	var isEmpty = true;
	for (var i = 0; i < boxes.length; i++) { // loop through the checkboxes
		if (boxes[i].checked) { // the checkbox is checked
		isEmpty = false; // a box is checked
		}
	}
    
    if (registration.other.value.length > 1)
	{
		isEmpty = false;
	}
    
	if (isEmpty) {
		alert('No checkboxes were checked!');
		return false;
	}
}
</script>
<?php get_header(); ?>

<div id="content">
<?php include 'single_sidebar.php';?>
<div id="content-main-single">
  <?php if (have_posts()) : ?>
  <?php while (have_posts()) : the_post(); ?>
  <div class="post" id="post-<?php the_ID(); ?>">
    <div class="posttitle">
      <h2>
        <?php the_title(); ?>
      </h2>
    </div>
    <?php /*If form has been submitted*/
			if ($_SERVER['REQUEST_METHOD'] == 'POST') : ?>
    <?php /* Start Captcha */
	require_once('recaptchalib.php');
	$privatekey = "6LejMgEAAAAAACOccJz6aBCZ6H1_C-oOZgZ4onzh";
	$resp = recaptcha_check_answer ($privatekey,
                                $_SERVER["REMOTE_ADDR"],
                                $_POST["recaptcha_challenge_field"],
                                $_POST["recaptcha_response_field"]);

	if (!$resp->is_valid) {
	  die ("The reCAPTCHA wasn't entered correctly. Go back and try it again." .
       "(reCAPTCHA said: " . $resp->error . ")");
	}
	
		$pattern = '/.*@.*\..*/';
        $email   = $_POST['email'];
		$events = implode(';',$_POST['events']);
		
        if (preg_match($pattern, $_POST['email']) > 0 && strlen($_POST['fullname']) > 0 && strlen($_POST['project']) > 0) { 
				// Set Mail Variables
				$to      = "rt-software@ccs.ornl.gov";
				$subject = "NCCS Software Request: " . $_POST['software'];
				$message = "A new software installation request has been submitted:\n\n".$_POST['fullname']."\nEmail: ".$_POST['email']."\nAffiliation: ".$_POST['affiliation']."\nProject ID: ".$_POST['project']."\nPhone: ".$_POST['phone']."\nMachines Requested: ".implode(', ', $_POST['events'])."\nName of the application: ".$_POST['software']."\nDescription of software:\n".$_POST['description']."\n\nHow to obtain:\n".$_POST['obtaining']."\n\nJustification:\n".$_POST['justification']."\n\nUsers:\n".$_POST['users']."";
				$messageConfirmation = $_POST['fullname'].",\nThank you for contacting the NCCS. We have received your registration information and a copy of your information is listed below. If any of this is incorrect or if you need to get in touch with us for any reason, send an e-mail message to help@nccs.gov.\n\nName: ".$_POST['fullname']."\nEmail: ".$_POST['email']."\nAffiliation: ".$_POST['affiliation']."\nProject ID: ".$_POST['project']."\nPhone: ".$_POST['phone']."\nMachines Requested: ".implode(', ', $_POST['events'])."\nName of the application: ".$_POST['software']."\nDescription of software:\n".$_POST['description']."\n\nHow to obtain:\n".$_POST['obtaining']."\n\nJustification:\n".$_POST['justification']."\n\nUsers:\n".$_POST['users']."";
				$headers  = 'MIME-Version: 1.0' . "\r\n";
				$headers .= 'Content-type: text/html; charset=iso-8859-1' . "\r\n";
                $headers = 'From: NCCS Software Request <' .$_POST['email']. ">\r\n";
				$headers2  = 'MIME-Version: 1.0' . "\r\n";
				$headers2 .= 'Content-type: text/html; charset=iso-8859-1' . "\r\n";
				$headers2 = 'From: NCCS Software Request <noreply@nccs.gov>' . "\r\n";					

				mail($to, $subject, $message, $headers); //Sends Notice to NCCS Workshop Staff
				print "<br /><br /><div class=\"entry\"><strong>Thank you for contacting the NCCS.</strong></div>";
				mail($_POST['email'], $subject, $messageConfirmation, $headers2); //Sends Comfirmation Email to Individual Registering
		} else {
		print "The form information you submitted was either incomplete or invalid.  <a href=\"http://www-test1.nccs.gov/user-support/general-support/software-request-swtools/\">Please resubmit your registration</a>.";
		}
	?>
    <?php /*Else display the form*/ else : ?>
    <div class="entry"><strong>Please complete the form below in order to request a software/library/application installation on an NCCS computer.</strong> <br />
    <br />  
    <form action="<?php echo "http://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']; ?>" id="registration" name="registration" onSubmit="return validate(registration)" method="post">
        <br />
        <div class="registration-section">Personal Information</div>
        <div class="newfield"><span class="registration-option"><strong>Full Name:</strong> <span class="required">*</span></span> <span class="registration-field">
          <input name="fullname" type="text" maxlength="120" />
          </span></div>
        <div class="newfield"><span class="registration-option"><strong>Email Address:</strong> <span class="required">*</span></span> <span class="registration-field">
          <input name="email" type="text" maxlength="100" id="email" />
          </span></div>
        <div class="newfield"><span class="registration-option"><strong>Affiliation (Institution):</strong></span> <span class="registration-field">
          <input name="affiliation" type="text" maxlength="100" id="affiliation" />
          </span></div>
          <div class="newfield"><span class="registration-option"><strong>INCITE Project ID: </strong><span class="required">*</span></span> <span class="registration-field">
          <input name="project" type="text" maxlength="10" id="project" />
          </span></div>
        <div class="newfield"><span class="registration-option"><strong>Phone:</strong></span> <span class="registration-field">
          <input name="phone" type="text" maxlength="20" id="phone" />
          </span></div>
        <br />
        <br />
        <div class="registration-section">Additional Information</div>
        <div class="newfield"><span class="registration-option"><strong>Software Name: </strong><span class="required">*</span></span> <span class="registration-field">
                  <input name="software" type="text" maxlength="30" id="software" />
        </span></div>
        
        
        <div class="newfield"><span class="registration-option-long">Please give us a brief description of the software.  If the software is export controlled, we likely can not provide install it.  We may also decline to install licensed software under certain circumstances.  <span class="required">*</span></span></div>
        <br />
		<br />
        <span style="margin-left:30px;">
        <textarea name="description" rows="10" wrap="virtual"></textarea>
        </span> <br />
        
       
        <div class="newfield"><span class="registration-option-long">How can this software be obtained? <span class="required">*</span></span></div>
        <br />
		<br />
        <span style="margin-left:30px;">
        <textarea name="obtaining" rows="10" wrap="virtual"></textarea>
        </span> <br />
        
        
        <div class="newfield"><span class="registration-option-long">Why is this software needed? If NCCS provides equivalent software, what is different about this software? If requesting an upgrade, describe new features or bug fixes.<span class="required">*</span></span></div>
        <br />
		<br />
        <span style="margin-left:30px;">
        <textarea name="justification" rows="10" wrap="virtual"></textarea>
        </span> <br />
        
        <div class="newfield"><span class="registration-option-long">Who will be using this software?  Approximately how many people will be using it? If possible, list individual users of this software.  If the software is export controlled, we likely can not provide install it.  We may also decline to install licensed software under certain circumstances.  <span class="required">*</span></span></div>
        <br />
		<br />
        <span style="margin-left:30px;">
        <textarea name="users" rows="10" wrap="virtual"></textarea>
        </span> <br />
        
        <div class="newfield"><span class="registration-option">Machines Requested: <span class="required">*</span></span>
        <span class="registration-field-buttons"><input type="checkbox" value="XT" name="events[]"/ >&nbsp;Jaguar</span>
        </div>
        
        <div class="newfield"><span class="registration-option">&nbsp;</span>
        <span class="registration-field-buttons"><input type="checkbox" value="Lens" name="events[]"  />&nbsp;Lens</span>
        </div>
        
        <div class="newfield"><span class="registration-option">&nbsp;</span>
        <span class="registration-field-buttons"><input type="checkbox" value="Smoky" name="events[]"  />&nbsp;Smoky</span>                  
        </div>
        
        <div class="newfield"><span class="registration-option">&nbsp;</span>
        <span class="registration-field-buttons"><input type="checkbox" value="Eugene" name="events[]"  />&nbsp;Eugene</span>                  
        </div>
        
        <div class="newfield"><span class="registration-option">&nbsp;</span> 
        <span class="registration-field-buttons"><input type="checkbox" value="Ewok" name="events[]"  />&nbsp;Ewok</span>
        </div>
            
        <div class="newfield"><span class="registration-option">Other system:</span>
        <span class="registration-field-buttons"><input type="textbox" maxlength="10" id ="other"  name="events[]"  /></span>
        </div>
        <br />
        <br />
        <div class="registration-section">Verification</div>
        <div class="newfield"><span class="registration-option"><strong>Verification:</strong> <span class="required">*</span></span> <span class="registration-field">
         </div>
         <?php require_once('recaptchalib.php');
            $publickey = "6LejMgEAAAAAAKuvojQx9lx5uiKEY-4-Op_E6GXh"; // you got this from the signup page
            echo recaptcha_get_html($publickey); 
            ?>
          </span>
        <div class="content-buttons">
          <input name="submit" type="submit" value="Submit" />
        </div>
      </form>
      For additional questions please contact <a href="mailto:help@nccs.gov">NCCS Help</a></div>
    <?php endif; ?>
    <?php endwhile; ?>
  </div>
  <?php endif; ?>
</div>
<?php get_footer(); ?>
