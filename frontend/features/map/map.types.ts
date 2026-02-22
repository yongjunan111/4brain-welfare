// features/map/map.types.ts

export interface Location {
    lat: number;
    lng: number;
}

export interface MapFacility {
    id: string;
    name: string;
    category: "복지시설" | "보육/교육시설" | "공공기관" | "의료기관" | "편의시설" | "기타" | "청년센터";
    address: string;
    phone?: string;
    location: Location;
    description?: string;
}

export interface MapFilterState {
    category: string | "전체";
    search: string;
    center?: Location;
}
