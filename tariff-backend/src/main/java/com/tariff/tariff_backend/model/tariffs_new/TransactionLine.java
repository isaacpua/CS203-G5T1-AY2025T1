package com.tariff.tariff_backend.model.tariffs_new;

import java.math.BigDecimal;
import java.time.Instant;

import org.hibernate.annotations.CreationTimestamp;

import com.tariff.tariff_backend.model.User;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "transaction_line", schema = "tariffs")
@Schema(description = "Transaction record storing user tariff calculations")
public class TransactionLine {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "transactionid")
    @Schema(description = "Unique transaction identifier", example = "67890")
    private Integer transactionId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "userid", nullable = false)
    @Schema(description = "User who performed the calculation", required = true)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "tariffid", nullable = false)
    @Schema(description = "Tariff used in the calculation", required = true)
    private Tariff tariff;

    @Column(name = "value", nullable = false)
    @Schema(description = "Calculated duty amount in the applicable currency", example = "1250.75", required = true)
    private BigDecimal calculatedValue;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    @Schema(description =  "Time Tariff was created")
    private Instant created_at;
}
