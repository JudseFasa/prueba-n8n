import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://mvsnymlcqutxnmnfxdgt.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im12c255bWxjcXV0eG5tbmZ4ZGd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1MjE1ODksImV4cCI6MjA4MDA5NzU4OX0.mNPS7-1YXUUM9XhVYvsg6urhnxP9Zx8BydvsGhD8qBU'

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Import the supabase client like this:
// For React:
// import { supabase } from "@/integrations/supabase/client";
// For React Native:
// import { supabase } from "@/src/integrations/supabase/client";
