<?php
/*
Template Name: Software Status - XT
*/
?>
<?php get_header();?>
<div id="content">
<?php include 'single_sidebar.php';?>
<div id="content-main-single">
<?php if (have_posts()) : ?>
		
		<?php while (have_posts()) : the_post(); ?>
				
			<div class="post" id="post-<?php the_ID(); ?>">
				<div class="posttitle">
					<h2>
                    
                    <?php 
                    if ($_GET["software"] == "") {
                        the_title(); 
                        }
                    ?>
                    
                    </h2>


</div>
				
				<div class="entry">
					


                <style type="text/css">
        
                
                /*
                table.inline {
                    padding: 0px;
                    padding-top: 0px;
                    padding-bottom: 0px;
                }
                */
                                                   
                
                table.inline td.hidden {
                    border: 0px; 
                    text-align: left;
                }

                table.inline td.hidden2 {
                    border: 0px; 
                    width: 5px;
                    padding-left: 20px;
                    text-align: right;
                }

                ul.sw li {
                    font: bold 11px "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
                    text-transform: uppercase; 
                }
                
                </style>

                
                
                    <?php 
                    
                        if (($_GET["software"] == "")  && ($_GET["view"] == "") ){
                            the_content(); 
                            include('/sw/tools/www/xt/alphabetical.html');
                        }elseif ( ($_GET["software"] == "") && ($_GET["view"] == "category") ){
                            the_content();
                            include('/sw/tools/www/xt/category.html');
                        }elseif ($_GET["software"] != "" ){
                            include('/sw/tools/www/xt/' . $_GET["software"]  .'.html');
                        }
                    ?> 
                                                                                                                                                                                     
                
                    
                    <?php wp_link_pages(); ?>				
					<?php $sub_pages = wp_list_pages( 'sort_column=menu_order&depth=1&title_li=&echo=0&child_of=' . $id );?>
					<?php /*?><?php if ($sub_pages <> "" ){?>
						<p class="post-info">This page has the following sub pages.</p>
						<ul><?php echo $sub_pages; ?></ul>
					<?php }?>			<?php */?>								
				</div>
		
		
				<?php /*?><?php comments_template(); ?><?php */?>
			</div>
	
		<?php endwhile; ?>

		<p align="center"><?php posts_nav_link(' - ','&#171; Prev','Next &#187;') ?></p>
		
	<?php else : ?>

		<h2 class="center">Not Found</h2>
		<p class="center">Sorry, but you are looking for something that isn't here.</p>
		

	<?php endif; ?>
</div><!-- end id:content-main -->
<?php get_footer();?>
