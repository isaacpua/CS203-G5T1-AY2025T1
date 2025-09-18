package com.tariff.tariff_backend.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Entity
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Table(name="role", schema = "tariffs") // where to look for the entity


public class Role {
    @Id
    private Integer id;
    @Column(unique = true, nullable = false)
    private String name;
}
