package com.tariff.tariff_backend.model.dashboard;

import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class DashboardResponse {
    
    private Boolean success;
    private String message;
}
