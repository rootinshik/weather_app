import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface SavedCity {
  id: string;
  city_name: string;
  latitude: number;
  longitude: number;
  country: string;
  state?: string;
  order_index: number;
  created_at: string;
}

export const getSavedCities = async (): Promise<SavedCity[]> => {
  const { data, error } = await supabase
    .from('saved_cities')
    .select('*')
    .order('order_index', { ascending: true });

  if (error) throw error;
  return data || [];
};

export const addSavedCity = async (city: {
  city_name: string;
  latitude: number;
  longitude: number;
  country: string;
  state?: string;
}): Promise<SavedCity> => {
  const { data: existingCities } = await supabase
    .from('saved_cities')
    .select('order_index')
    .order('order_index', { ascending: false })
    .limit(1);

  const nextOrderIndex = existingCities && existingCities.length > 0
    ? existingCities[0].order_index + 1
    : 0;

  const { data, error } = await supabase
    .from('saved_cities')
    .insert([{ ...city, order_index: nextOrderIndex }])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const deleteSavedCity = async (id: string): Promise<void> => {
  const { error } = await supabase
    .from('saved_cities')
    .delete()
    .eq('id', id);

  if (error) throw error;
};
