import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

interface DrillSelection {
  stateId: string | null;
  stateName: string | null;
  districtId: string | null;
  districtName: string | null;
  cityId: string | null;
  cityName: string | null;
  locationId: string | null;
}

interface AppValue extends DrillSelection {
  selectedBank: string;
  setSelectedBank: (b: string) => void;
  reportOpen: boolean;
  setReportOpen: (v: boolean) => void;
  reportScope: "bank" | "state" | "district" | "city" | "location";
  setReportScope: (s: "bank" | "state" | "district" | "city" | "location") => void;
  navOpen: boolean;
  setNavOpen: (v: boolean) => void;
  toggleNav: () => void;
  selectState: (id: string | null, name: string | null) => void;
  selectDistrict: (id: string | null, name: string | null) => void;
  selectCity: (id: string | null, name: string | null) => void;
  selectLocation: (id: string | null) => void;
}

const AppContext = createContext<AppValue | null>(null);

const EMPTY: DrillSelection = {
  stateId: null, stateName: null, districtId: null, districtName: null,
  cityId: null, cityName: null, locationId: null,
};

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedBank, setSelectedBank] = useState("HDFC Bank");
  const [reportOpen, setReportOpen] = useState(false);
  const [reportScope, setReportScope] = useState<AppValue["reportScope"]>("bank");
  const [navOpen, setNavOpen] = useState(false);
  const [drill, setDrill] = useState<DrillSelection>(EMPTY);

  const value = useMemo<AppValue>(
    () => ({
      ...drill,
      selectedBank,
      setSelectedBank,
      reportOpen,
      setReportOpen,
      reportScope,
      setReportScope,
      navOpen,
      setNavOpen,
      toggleNav: () => setNavOpen((v) => !v),
      // Selecting a level always clears the levels below it — a stale child id would
      // query data that does not belong to the new parent.
      selectState: (id, name) =>
        setDrill({ ...EMPTY, stateId: id, stateName: name }),
      selectDistrict: (id, name) =>
        setDrill((d) => ({ ...d, districtId: id, districtName: name, cityId: null, cityName: null, locationId: null })),
      selectCity: (id, name) =>
        setDrill((d) => ({ ...d, cityId: id, cityName: name, locationId: null })),
      selectLocation: (id) => setDrill((d) => ({ ...d, locationId: id })),
    }),
    [drill, selectedBank, reportOpen, reportScope, navOpen],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
