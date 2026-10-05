import { Route, Routes } from "react-router-dom";

import Layout from "@/components/layout/Layout";
import { Toaster } from "@/components/ui/sonner";
import { AppProvider } from "@/context/AppContext";
import Comparison from "@/pages/Comparison";
import Consultant from "@/pages/Consultant";
import Dashboard from "@/pages/Dashboard";
import LocationIntelligence from "@/pages/LocationIntelligence";
import Methodology from "@/pages/Methodology";
import ModelLab from "@/pages/ModelLab";
import Network from "@/pages/Network";
import OpportunityMap from "@/pages/OpportunityMap";
import Recommendations from "@/pages/Recommendations";

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <AppProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="location-intelligence" element={<LocationIntelligence />} />
          <Route path="comparison" element={<Comparison />} />
          <Route path="network" element={<Network />} />
          <Route path="opportunity-map" element={<OpportunityMap />} />
          <Route path="consultant" element={<Consultant />} />
          <Route path="recommendations" element={<Recommendations />} />
          <Route path="model" element={<ModelLab />} />
          <Route path="methodology" element={<Methodology />} />
        </Route>
      </Routes>
      <Toaster />
    </AppProvider>
  );
}
