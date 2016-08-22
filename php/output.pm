{
   my $header;
   my $detail;

# ---------------------------------------------------------------------------
sub out_init
{
   if (! defined($header))
   {
      if ($HTML)
      {
         $header = "out_header_html";
         $detail = "out_detail_html";
      }
      else
      {
         $header = "out_header_text";
         $detail = "out_detail_text";
      }
   }
}

# ---------------------------------------------------------------------------
sub out_header
{
   my ($format, $string);

   $format = shift(@_);
   $string = sprintf($format, @_);

   if ($HTML)
   {
      out_header_html($string);
   }
   else
   {
      out_header_text($string);
   }
}

# ---------------------------------------------------------------------------
sub out_detail
{
   my ($format, $string);

   $format = shift(@_);
   $string = sprintf($format, @_);

   if ($HTML)
   {
      out_detail_html($string);
   }
   else
   {
      out_detail_text($string);
   }
}

# ---------------------------------------------------------------------------
sub out_header_html
{
   my ($string);

   ($string) = @_;

   if ($detail)
   {
      print("</blockquote>\n");
      $detail = 0;
   }
   $header = "<p><h3>$string</h3><blockquote>\n";
}

# ---------------------------------------------------------------------------
sub out_header_text
{
   my ($string);

   ($string) = @_;

   $header = "\n${string}\n";
}

# ---------------------------------------------------------------------------
sub out_detail_html
{
   my ($string);

   ($string) = @_;

   if ($header ne "")
   {
      print($header);
      $header = "";
   }
   print("<br>${string}\n");
   $detail = 1;
}

# ---------------------------------------------------------------------------
sub out_detail_text
{
   my ($string);

   ($string) = @_;

   if ($header ne "")
   {
      print($header);
      $header = "";
   }
   print("   $string\n");
}
}

1;
