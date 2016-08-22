<?php
/*
Template Name: Software Description
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
					<h2><?php the_title(); ?></h2>


</div>
				
				<div class="entry">
                    
                
                    
                    <!-- SWTOOLS CDOE -->
                    <style type="text/css">
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
                                                    
                    </style>
                    
                    
                    
                    <?php include ("/sw/tools/www/" . $_GET["arch"] . "/" . $_GET["software"] . ".html") ;  ?> 
					
                    <!--END SWTOOLS CODE-->
                    
                    
                    <?php the_content(); ?>
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
