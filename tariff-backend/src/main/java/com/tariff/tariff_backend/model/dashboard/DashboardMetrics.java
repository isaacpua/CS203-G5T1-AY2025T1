package com.tariff.tariff_backend.model.dashboard;

import java.util.List;

import com.tariff.tariff_backend.model.Tariff;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DashboardMetrics {
    private List<Tariff> content;
    private int number;
    private int totalPages;
    private long totalElements;
}
