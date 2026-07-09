import React, { useState, useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import { setField } from "../store/slices/interactionSlice";
import { searchHCPs } from "../api/client";

export default function HCPSearch({ value }) {
  const dispatch = useDispatch();
  const [query, setQuery] = useState(value || "");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => setQuery(value || ""), [value]);

  useEffect(() => {
    function onClickOutside(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }
    const handle = setTimeout(() => {
      searchHCPs(query)
        .then(setResults)
        .catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(handle);
  }, [query]);

  const handleSelect = (hcp) => {
    setQuery(hcp.name);
    dispatch(setField({ field: "hcpName", value: hcp.name }));
    setOpen(false);
  };

  const handleChange = (e) => {
    setQuery(e.target.value);
    dispatch(setField({ field: "hcpName", value: e.target.value }));
    setOpen(true);
  };

  return (
    <div className="autocomplete" ref={boxRef}>
      <input
        className="text-input"
        placeholder="Search or select HCP..."
        value={query}
        onChange={handleChange}
        onFocus={() => setOpen(true)}
      />
      {open && results.length > 0 && (
        <div className="autocomplete-dropdown">
          {results.map((hcp) => (
            <div key={hcp.id} className="autocomplete-item" onClick={() => handleSelect(hcp)}>
              <span className="autocomplete-name">{hcp.name}</span>
              <span className="autocomplete-meta">
                {hcp.specialty}
                {hcp.hospital ? ` · ${hcp.hospital}` : ""}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
