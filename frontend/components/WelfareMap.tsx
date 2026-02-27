'use client';

import { useEffect, useState } from 'react';
import Script from 'next/script';
import { Map, MapMarker, CustomOverlayMap } from 'react-kakao-maps-sdk';

interface POI {
    id: number;
    name: string;
    latitude: number;
    longitude: number;
    address: string;
    phone: string;
    detail_url: string;
    theme: string; // theme ID or Name
}

const KAKAO_SDK_URL = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_MAP_API_KEY}&libraries=services,clusterer&autoload=false`;

export default function WelfareMap() {
    const [loaded, setLoaded] = useState(false);
    const [pois, setPois] = useState<POI[]>([]);
    const [selectedPoi, setSelectedPoi] = useState<POI | null>(null);

    useEffect(() => {
        // Fetch POIs from backend
        fetch('/api/policies/map/pois/')
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch map data');
                return res.json();
            })
            .then(data => {
                console.log("Map Data Fetched:", data);
                setPois(data);
            })
            .catch(err => console.error("Error fetching map POIs:", err));
    }, []);

    return (
        <>
            <Script
                src={KAKAO_SDK_URL}
                strategy="afterInteractive"
                onLoad={() => {
                    window.kakao.maps.load(() => setLoaded(true));
                }}
            />

            <div className="w-full h-[500px] bg-gray-100 rounded-lg overflow-hidden shadow-lg relative">
                {!loaded && (
                    <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                        지도를 불러오는 중입니다...
                    </div>
                )}

                {loaded && (
                    <Map
                        center={{ lat: 37.5665, lng: 126.9780 }} // Seoul City Hall
                        style={{ width: "100%", height: "100%" }}
                        level={7}
                    >
                        {pois.map((poi) => (
                            <MapMarker
                                key={poi.id}
                                position={{ lat: poi.latitude, lng: poi.longitude }}
                                onClick={() => setSelectedPoi(poi)}
                            />
                        ))}

                        {selectedPoi && (
                            <CustomOverlayMap
                                position={{ lat: selectedPoi.latitude, lng: selectedPoi.longitude }}
                                yAnchor={1} // Position above the marker
                            >
                                <div className="bg-white p-4 rounded-lg shadow-xl border border-gray-200 min-w-[200px] transform -translate-y-12">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="font-bold text-lg text-gray-800">{selectedPoi.name}</h3>
                                        <button
                                            onClick={() => setSelectedPoi(null)}
                                            className="text-gray-400 hover:text-gray-600"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-1">{selectedPoi.address}</p>
                                    {selectedPoi.phone && (
                                        <p className="text-sm text-blue-600 mb-2">📞 {selectedPoi.phone}</p>
                                    )}
                                    {selectedPoi.detail_url && (
                                        <a
                                            href={selectedPoi.detail_url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="block text-center bg-blue-500 text-white py-1 px-3 rounded text-sm hover:bg-blue-600 transition-colors"
                                        >
                                            상세보기
                                        </a>
                                    )}
                                    {/* Triangle pointer at bottom */}
                                    <div className="absolute bottom-[-8px] left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[8px] border-t-white filter drop-shadow-sm"></div>
                                </div>
                            </CustomOverlayMap>
                        )}
                    </Map>
                )}
            </div>
        </>
    );
}
